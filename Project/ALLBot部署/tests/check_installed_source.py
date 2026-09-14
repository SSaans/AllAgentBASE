"""Offline checks against installed AstrBot source; no app startup or network calls.

Run with Python and --core pointing to the installed core directory.
These checks exercise selected source methods with synthetic dependencies.
They do not replace QQ delivery, LLM, or visual acceptance.
"""
import argparse
import ast
import logging
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

parser = argparse.ArgumentParser()
parser.add_argument('--core', type=Path, required=True)
args, remaining = parser.parse_known_args()
CORE = args.core
PLUGIN = CORE / 'data/plugins/astrbot_plugin_qq_group_daily_analysis'
LOG = logging.getLogger('allbot-test')
LOG.addHandler(logging.NullHandler())


def load_nodes(path, selector, namespace):
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    nodes = selector(tree)
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), 'exec'), namespace)
    return namespace


def method(path, name, namespace):
    return load_nodes(path, lambda tree: [next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)], namespace)[name]


class Checks(unittest.IsolatedAsyncioTestCase):
    async def test_empty_whitelist_allows_normal_member(self):
        ns = {'logger': LOG, 'MessageType': types.SimpleNamespace(GROUP_MESSAGE='group', FRIEND_MESSAGE='friend')}
        process = method(CORE/'astrbot/core/pipeline/whitelist_check/stage.py', 'process', ns)
        event = types.SimpleNamespace(stop_event=lambda: self.fail('Unexpected block'))
        await process(types.SimpleNamespace(enable_whitelist_check=True, whitelist=[]), event)

    async def test_nonempty_whitelist_blocks_unlisted_member(self):
        ns = {'logger': LOG, 'MessageType': types.SimpleNamespace(GROUP_MESSAGE='group', FRIEND_MESSAGE='friend')}
        process = method(CORE/'astrbot/core/pipeline/whitelist_check/stage.py', 'process', ns)
        stopped = []
        event = types.SimpleNamespace(role='member', unified_msg_origin='test:GroupMessage:other', get_platform_name=lambda:'aiocqhttp', get_group_id=lambda:'other', stop_event=lambda:stopped.append(True))
        stage = types.SimpleNamespace(enable_whitelist_check=True, whitelist=['allowed'], wl_ignore_admin_on_group=False, wl_ignore_admin_on_friend=False, wl_log=False)
        await process(stage,event)
        self.assertEqual(stopped,[True])

    async def test_persona_disabled_reproduces_missing_prompt(self):
        fn = method(PLUGIN/'src/infrastructure/analysis/analyzers/base_analyzer.py','_build_system_prompt',{'logger':LOG})
        config = types.SimpleNamespace(get_use_plugin_specific_persona=lambda:False,get_plugin_specific_persona_id=lambda:'',get_keep_original_persona=lambda:False)
        obj = types.SimpleNamespace(config_manager=config,context=types.SimpleNamespace(persona_manager=object()))
        self.assertIsNone(await fn(obj,'test:GroupMessage:synthetic'))

    async def test_persona_enabled_inherits_default_prompt(self):
        fn = method(PLUGIN/'src/infrastructure/analysis/analyzers/base_analyzer.py','_build_system_prompt',{'logger':LOG})
        config = types.SimpleNamespace(get_use_plugin_specific_persona=lambda:False,get_plugin_specific_persona_id=lambda:'',get_keep_original_persona=lambda:True)
        manager=types.SimpleNamespace(get_default_persona_v3=AsyncMock(return_value={'prompt':'synthetic persona'}))
        obj=types.SimpleNamespace(config_manager=config,context=types.SimpleNamespace(persona_manager=manager))
        api=types.ModuleType('astrbot.api'); api.sp=types.SimpleNamespace(get_async=AsyncMock(return_value={}))
        with patch.dict(sys.modules,{'astrbot.api':api}):
            self.assertEqual(await fn(obj,'test:GroupMessage:synthetic'),'synthetic persona')

    async def test_empty_provider_falls_back_to_session(self):
        session=AsyncMock(return_value='synthetic-provider')
        first=AsyncMock(return_value='wrong-provider')
        fn=method(PLUGIN/'src/infrastructure/analysis/utils/llm_utils.py','get_provider_id_with_fallback',{'logger':LOG,'TraceContext':types.SimpleNamespace(current=lambda:None),'_try_get_session_provider_id':session,'_try_get_first_available_provider_id':first})
        config=types.SimpleNamespace(get_llm_provider_id=lambda:'')
        self.assertEqual(await fn(object(),config,None,'synthetic'),'synthetic-provider')
        first.assert_not_awaited()

    async def test_missing_session_provider_uses_first_available(self):
        fn=method(PLUGIN/'src/infrastructure/analysis/utils/llm_utils.py','get_provider_id_with_fallback',{'logger':LOG,'TraceContext':types.SimpleNamespace(current=lambda:None),'_try_get_session_provider_id':AsyncMock(return_value=None),'_try_get_first_available_provider_id':AsyncMock(return_value='first')})
        self.assertEqual(await fn(object(),types.SimpleNamespace(get_llm_provider_id=lambda:''),None,None),'first')

    async def test_scheduled_analysis_empty_whitelist_is_disabled(self):
        fn=method(PLUGIN/'src/infrastructure/config/config_manager.py','is_auto_analysis_enabled',{})
        obj=types.SimpleNamespace(get_scheduled_group_list_mode=lambda:'whitelist',get_scheduled_group_list=lambda:[])
        self.assertFalse(fn(obj))

    async def test_forward_boundaries_use_actual_source_branch(self):
        path=CORE/'astrbot/core/pipeline/result_decorate/stage.py'
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        branches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and 'event.get_platform_name()' in ast.unparse(n.test) and 'aiocqhttp' in ast.unparse(n.test) and any(isinstance(k,ast.Name) and k.id=='word_cnt' for k in ast.walk(n))]
        self.assertEqual(len(branches),1)
        class Plain:
            def __init__(self,text): self.text=text
        class Node:
            def __init__(self,**kwargs): self.__dict__.update(kwargs)
        for threshold,length,forward in [(1500,1499,False),(1500,1500,False),(1500,1501,True),(10,10,False),(10,11,True)]:
            with self.subTest(threshold=threshold,length=length):
                result=types.SimpleNamespace(chain=[Plain('测'*length)])
                event=types.SimpleNamespace(get_platform_name=lambda:'aiocqhttp',get_self_id=lambda:'synthetic-bot')
                ns={'event':event,'result':result,'self':types.SimpleNamespace(forward_threshold=threshold),'Plain':Plain,'Node':Node}
                exec(compile(ast.Module(body=branches,type_ignores=[]),str(path),'exec'),ns)
                self.assertEqual(isinstance(result.chain[0],Node),forward)
                if forward:self.assertEqual(result.chain[0].content[0].text,'测'*length)


if __name__=='__main__':
    unittest.main(argv=[sys.argv[0],*remaining],verbosity=2)
