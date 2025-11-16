#!/usr/bin/env python3
"""
AuViMa CLI - Chrome DevTools Protocol 命令行接口

提供向后兼容的CLI接口，支持所有原Shell脚本功能。
"""

import sys
import click
from typing import Optional

from .commands import (
    navigate,
    click_element,
    screenshot,
    execute_javascript,
    get_title,
    scroll,
    wait,
    zoom,
    clear_effects,
    highlight,
    pointer,
    spotlight,
    annotate
)


@click.group()
@click.option(
    '--debug', 
    is_flag=True, 
    help='启用调试模式，输出详细日志'
)
@click.option(
    '--timeout', 
    type=int, 
    default=30,
    help='设置操作超时时间（秒），默认30秒'
)
@click.option(
    '--host',
    type=str,
    default='127.0.0.1',
    help='Chrome DevTools Protocol 主机地址，默认127.0.0.1'
)
@click.option(
    '--port',
    type=int,
    default=9222,
    help='Chrome DevTools Protocol 端口，默认9222'
)
@click.pass_context
def cli(ctx, debug: bool, timeout: int, host: str, port: int):
    """
    AuViMa - Chrome DevTools Protocol 命令行工具
    
    提供与Chrome浏览器交互的命令行接口，支持页面导航、
    元素操作、截图、JavaScript执行等功能。
    """
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    ctx.obj['TIMEOUT'] = timeout
    ctx.obj['HOST'] = host
    ctx.obj['PORT'] = port
    
    if debug:
        click.echo(f"调试模式已启用 - 主机: {host}:{port}, 超时: {timeout}s")


# 注册所有子命令
cli.add_command(navigate)
cli.add_command(click_element)
cli.add_command(screenshot)
cli.add_command(execute_javascript)
cli.add_command(get_title)
cli.add_command(scroll)
cli.add_command(wait)
cli.add_command(zoom)
cli.add_command(clear_effects)
cli.add_command(highlight)
cli.add_command(pointer)
cli.add_command(spotlight)
cli.add_command(annotate)


def main():
    """CLI入口点"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n操作已取消", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()