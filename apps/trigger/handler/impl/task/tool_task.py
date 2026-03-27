# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： application_task.py
    @date：2026/1/14 19:14
    @desc:
"""
import json
import time
import traceback

import uuid_utils.compat as uuid
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from application.flow.common import Workflow, WorkflowMode
from application.flow.i_step_node import ToolWorkflowPostHandler
from application.flow.tool_workflow_manage import ToolWorkflowManage
from application.serializers.common import ToolExecute
from common.utils.logger import maxkb_logger
from common.utils.rsa_util import rsa_long_decrypt
from common.utils.tool_code import ToolExecutor
from knowledge.models.knowledge_action import State
from tools.models import Tool, ToolRecord, ToolTaskTypeChoices, ToolWorkflow
from tools.serializers.tool_workflow import ToolWorkflowSerializer
from trigger.handler.base_task import BaseTriggerTask
from trigger.handler.impl.task.application_task import get_user_field_component_input_type, get_field_value
from trigger.models import TaskRecord

executor = ToolExecutor()


def get_reference(fields, obj):
    for field in fields:
        value = obj.get(field)
        if value is None:
            return None
        else:
            obj = value
    return obj


def _convert_value(_type, value):
    if value is None:
        return None

    if _type == 'int':
        return int(value)
    if _type == 'boolean':
        value = 0 if ['0', '[]'].__contains__(value) else value
        return bool(value)
    if _type == 'float':
        return float(value)
    if _type == 'dict':
        v = json.loads(value)
        if isinstance(v, dict):
            return v
        raise Exception(_('type error'))
    if _type == 'array':
        v = json.loads(value)
        if isinstance(v, list):
            return v
        raise Exception(_('type error'))
    return value


def get_tool_parameters_setting(tool):
    tool_parameter_setting = {f.get("name"): f.get("type") for f in (tool.get('input_field_list') or []) if
                              f.get("name")}

    if tool.get('tool_type') == 'CUSTOM':
        return tool_parameter_setting
    elif tool.get('tool_type') == 'WORKFLOW':
        work_flow = tool.get('work_flow') or {}
        base_node_list = [n for n in work_flow.get('nodes', []) if n.get('type') == "tool-base-node"]
        if len(base_node_list) == 0:
            raise Exception('Incorrect tool workflow information')
        base_node = base_node_list[0]
        user_input_field_list = base_node.get('properties', {}).get('user_input_field_list') or []
        user_input_field_list = {user_field.get('field'): {
            'required': user_field.get('is_required'),
            'default_value': user_field.get('default_value'),
            'type': get_user_field_component_input_type(user_field.get('input_type'))
        } for user_field in user_input_field_list}
        tool_parameter_setting['user_input_field_list'] = user_input_field_list
        return tool_parameter_setting


def get_tool_execute_parameters(parameter_setting, tool_parameters_setting, kwargs):
    many_field = ['user_input_field_list']
    parameters = {'form_data': {}}
    for key, value in tool_parameters_setting.items():
        setting = parameter_setting.get(key)
        if setting:
            if many_field.__contains__(key):
                for ck, cv in value.items():
                    _setting = setting.get(ck)
                    if _setting:
                        _value = get_field_value(_setting, kwargs, cv.get('type'), cv.get('required'),
                                                 cv.get('default_value'), ck)
                        parameters['form_data'][ck] = _value
                    else:
                        if cv.get('default_value'):
                            parameters['form_data'][ck] = cv.get('default_value')
                        else:
                            if cv.get('is_required'):
                                raise Exception(f'{ck} is required')
            else:
                value = get_field_value(setting, kwargs, value.get('type'), value.get('is_required'),
                                        value.get('default_value'), key)
                parameters['message' if key == 'question' else key] = value
        else:
            if value.get('default_value'):
                parameters['message' if key == 'question' else key] = value.get('default_value')
            else:
                if value.get('is_required'):
                    raise Exception(f'{"message" if key == "question" else key} is required')

    return parameters


def get_loop_workflow_node(node_list):
    result = []
    for item in node_list:
        if item.get('type') == 'loop-node':
            for loop_item in item.get('loop_node_data') or []:
                for inner_item in loop_item.values():
                    result.append(inner_item)
    return result


def get_workflow_state(details):
    node_list = details.values()
    all_node = [*node_list, *get_loop_workflow_node(node_list)]
    err = any([True for value in all_node if value.get('status') == 500 and not value.get('enableException')])
    if err:
        return State.FAILURE
    return State.SUCCESS


def _get_result_detail(result):
    if isinstance(result, dict):
        result_dict = {k: (str(v)[:500] if len(str(v)) > 500 else v) for k, v in result.items()}
    elif isinstance(result, list):
        result_dict = [str(item)[:500] if len(str(item)) > 500 else item for item in result]
    elif isinstance(result, str):
        result_dict = result[:500] if len(result) > 500 else result
    else:
        result_dict = result
    return result_dict


class ToolTask(BaseTriggerTask):
    def support(self, trigger_task, **kwargs):
        return trigger_task.get('source_type') == 'TOOL'

    def execute(self, trigger_task, **kwargs):
        parameter_setting = trigger_task.get('parameter')
        tool_id = trigger_task.get('source_id')
        task_record_id = uuid.uuid7()
        start_time = time.time()
        try:
            tool = QuerySet(Tool).filter(id=tool_id, is_active=True).first()
            if not tool:
                maxkb_logger.info(f"Tool with id {tool_id} not found or inactive.")
                return
            tool = {field.name: getattr(tool, field.name) for field in tool._meta.fields}
            if tool.get('tool_type') == 'WORKFLOW':
                workflow = QuerySet(ToolWorkflow).filter(
                    tool_id=tool_id,
                    is_publish=True,
                    tool__is_active=True
                ).select_related('tool').first()
                if workflow:
                    tool['work_flow'] = workflow.work_flow

            TaskRecord(
                id=task_record_id,
                trigger_id=trigger_task.get('trigger'),
                trigger_task_id=trigger_task.get('id'),
                source_type="TOOL",
                source_id=tool_id,
                task_record_id=task_record_id,
                meta={'input': parameter_setting, 'output': {}},
                state=State.STARTED
            ).save()
            ToolRecord(
                id=task_record_id,
                workspace_id=tool.get('workspace_id'),
                tool_id=tool.get('id'),
                source_type=ToolTaskTypeChoices.TRIGGER,
                source_id=trigger_task.get('trigger'),
                meta={'input': parameter_setting, 'output': {}},
                state=State.STARTED
            ).save()
            tool_parameters_setting = get_tool_parameters_setting(tool)
            parameters = get_tool_execute_parameters(parameter_setting, tool_parameters_setting, kwargs)
            init_params_default_value = {i["field"]: i.get('default_value') for i in tool.get('init_field_list')}

            if tool.get('init_params') is not None:
                all_params = init_params_default_value | json.loads(
                    rsa_long_decrypt(tool.get('init_params'))) | parameters
            else:
                all_params = init_params_default_value | parameters
            result = None
            if tool.get('tool_type') == 'WORKFLOW':
                tool_record_id = str(uuid.uuid7())
                took_execute = ToolExecute(tool_id, tool_record_id,
                                           tool.get('workspace_id'),
                                           'trigger',
                                           tool_id,
                                           False)
                from application.flow.tool_workflow_manage import ToolWorkflowManage
                work_flow_manage = ToolWorkflowManage(
                    Workflow.new_instance(tool.get('work_flow'), WorkflowMode.TOOL),
                    {
                        'chat_record_id': task_record_id,
                        'tool_id': tool_id,
                        'stream': True,
                        'workspace_id': tool.get('workspace_id'),
                        **kwargs},

                    ToolWorkflowPostHandler(took_execute, tool_id),
                    is_the_task_interrupted=lambda: False,
                    child_node=None,
                    start_node_id=None,
                    start_node_data=None,
                    chat_record=None
                )
                res = work_flow_manage.run()
                for r in res:
                    pass
                result = work_flow_manage.out_context
            else:
                result = executor.exec_code(tool.get('code'), all_params)

            result_dict = _get_result_detail(result)

            maxkb_logger.debug(f"Tool execution result: {result}")

            QuerySet(TaskRecord).filter(id=task_record_id).update(
                state=State.SUCCESS,
                run_time=time.time() - start_time,
                meta={'input': parameter_setting, 'output': result_dict}
            )
            QuerySet(ToolRecord).filter(id=task_record_id).update(
                state=State.SUCCESS,
                run_time=time.time() - start_time,
                meta={'input': parameters, 'output': result_dict}
            )
        except Exception as e:
            maxkb_logger.error(f"Tool execution error: {traceback.format_exc()}")
            QuerySet(TaskRecord).filter(id=task_record_id).update(
                state=State.FAILURE,
                run_time=time.time() - start_time,
                meta={'input': parameter_setting, 'output': 'Error: ' + str(e), 'err_message': 'Error: ' + str(e)}
            )
            QuerySet(ToolRecord).filter(id=task_record_id).update(
                state=State.FAILURE,
                run_time=time.time() - start_time,
                meta={'input': parameter_setting, 'output': 'Error: ' + str(e), 'err_message': 'Error: ' + str(e)}
            )
