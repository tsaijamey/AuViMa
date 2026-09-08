/**
 * SessionRail — 左栏：新建会话、搜索、时间范围、状态筛选、会话清单、底部汇总。
 *
 * 三家（Claude Code / opencode / codex）的会话在核心数据层就合并排好了，这里不重排。
 *
 * **筛选是两个维度，不是一个。** 状态答「现在什么情况」，时间范围答「哪一段时间的」，
 * 两者并存、互不替代。按来源筛的那一维不在这里——一千多场 Claude Code 会话摆在一起，
 * 知道它们都来自 Claude Code 没有任何用；来源仍在每张卡上看得见，改由底部汇总报两家各几场。
 *
 * **搜索有两条腿。** 标题、目录、编号在本地即时筛，敲一个字就有反应；会话内容（提示词
 * 与 agent 回复正文）由服务端搜，慢一拍，所以它自己报进度、自己报哪里没搜全。两条的
 * 结果取并集，命中的那几场把命中的原话摆到卡片上。
 *
 * **状态与摘要一个字都不在这里推导。** 服务端已经判完四档、填好两格摘要，界面照着显示。
 * 摆两处判据迟早各走各的，那时中栏和左栏会对同一场会话说两种话。
 *
 * **选中态不用左侧竖条。** 整行换成品牌绿淡底、标题转品牌绿。单边竖条是肌肉记忆，
 * 不是设计决策。绿环后来也去掉了：淡底加标题转绿已经足够把那一行从一列灰字里分出来。
 *
 * **颜色一律走 CSS 变量。** 明暗两套主题各有一份品牌绿，写死色值会让其中一套失真。
 *
 * 底部汇总只报已经发生的绝对数：共几场、两家各几场。没有分母，也不该有。
 *
 * **列表走窗口化渲染。** 全量会话可能上千场，用 Virtuoso 只渲染视口内可见的卡片。
 *
 * **置顶区是一片自己说了算的地方。** 名单存在服务端（见 `useSessionPins`），次序照置顶
 * 的次序而不是活动时刻，数量不设上限，整片可以折起来。它**不跟状态与时间范围走**——那
 * 两道答的是「翻哪一段、翻哪一档」，而置顶答的是「这几场我随时要回来」，点一下「7 天」
 * 就让人挑出来的那几场消失，是把筛选的语义套到了一个不该被筛的地方。搜索另说：那一刻人
 * 是在找某一场，置顶区跟着筛才不会答非所问。
 *
 * 一场都没置顶时不长分区标题，整片仍是从前那个单列清单——空着的分区标题只是噪音。
 *
 * **分区标题是列表里的普通一行，不是窗口化列表的 group header。** group header 的位置要
 * 等列表量完每一行的高度才算得出来，量完之前那两行标题一个都不在页面上——真实浏览器里
 * 撞见过整片清单已经摆好、标题还没出现。标题上坐着折叠开关，它不该等任何东西。
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Virtuoso } from 'react-virtuoso';
import { ChevronDown, ChevronRight, Loader2, Mail, Pin, Plus, RefreshCw, Search, X } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import SessionItem, { resumeCommand } from './SessionItem';
import NewSessionModal from './NewSessionModal';
import { useSessionPins } from '@/hooks/useSessionPins';
import type { PendingLaunch } from '@/hooks/useAgentClients';
import type { SessionLaunch } from '@/hooks/useSessionLaunch';
import {
  DAY_OPTIONS,
  MIN_CONTENT_QUERY,
  STATUS_LABEL_KEY,
  type DayRange,
  type StatusFilter,
  type WorkbenchSession,
  type WorkbenchSessionsState,
} from '@/hooks/useWorkbenchSessions';

/**
 * 品牌绿承担选中、当前、活跃。三处共用一套，别处不许再造。
 *
 * **筛选那两行不在这三处之内。** 时间范围与状态是页面自己的操作面，不是数据。
 * 五个筛选档同时用品牌绿点亮，会让页面上常年挂着两块绿——真正需要被看见的
 * 「哪一场会话被选中了」「哪一场在跑」反而没有地方可去。所以选中的筛选档换成
 * 中性填充加一档字重，颜色留给数据。
 */
const ACCENT_TEXT = 'text-accent-primary';

/** 筛选档选中态：中性填充 + 字重。整块换底，不靠任何单边色条。 */
const CHIP_ON = 'bg-bg-active text-text-primary font-medium';
const CHIP_OFF = 'text-text-muted hover:bg-bg-hover hover:text-text-secondary';

/** 四档筛选加一个全部。次序与判定顺序一致，看的人不必再学一套排列。 */
const FILTERS: StatusFilter[] = ['all', 'running', 'error', 'done', 'idle'];

/** 筛选档的**词表键**。取字在渲染时做，换语言这一行跟着变。 */
const FILTER_LABEL_KEY: Record<StatusFilter, string> = {
  all: 'workbench.rail.filterAll',
  ...STATUS_LABEL_KEY,
};

/** 时间范围：不限，加四档。0 排在最前，与状态那一行的「全部」对齐。 */
const DAY_FILTERS: DayRange[] = [0, ...DAY_OPTIONS];

/**
 * 每一档点的颜色。与清单里那份保持一致（见 SessionItem 的同名表）：只有在跑与出错
 * 带颜色，已完成与停着用两级灰。图例与清单说的必须是同一套，否则人按图例去清单里找
 * 蓝点，会一个都找不到。
 */
const STATUS_DOT: Record<string, string> = {
  running: 'bg-accent-primary',
  error: 'bg-accent-error',
  done: 'bg-text-secondary',
  idle: 'bg-text-dim',
};

/** 列表里的一行：要么是分区标题，要么是一张会话卡。 */
type RailRow =
  | { kind: 'pinned-header' }
  | { kind: 'rest-header' }
  | { kind: 'session'; session: WorkbenchSession };

export interface SessionRailProps {
  state: WorkbenchSessionsState;
  selectedId: string | null;
  onSelect: (id: string) => void;
  /**
   * 正在起、还没进清单的那一场。有值就在清单上方摆一张启动卡——从点完创建到这一行
   * 真的长出来有将近十秒，那十秒里左栏什么都不说的话，人只会以为没建成。
   */
  launch?: SessionLaunch | null;
  /** 建出去了。等编号、反复重取清单这些事由页面那边的启动状态接手，左栏不自己等。 */
  onCreated?: (pending: PendingLaunch, text: string) => void;
  /**
   * 把没起来的那张卡收掉。
   *
   * 这个入口在左栏也要有：人在等的时候点开了别的会话，中栏就不再是那块启动面板，
   * 那边的收起按钮他够不着，而没起来的卡不会自己消失。
   */
  onDismissLaunch?: () => void;
}

export default function SessionRail({
  state,
  selectedId,
  onSelect,
  launch = null,
  onCreated,
  onDismissLaunch,
}: SessionRailProps) {
  const {
    sessions,
    visible,
    searched,
    counts,
    loading,
    error,
    search,
    setSearch,
    status,
    setStatus,
    days,
    setDays,
    content,
    reload,
  } = state;
  const { t } = useTranslation();
  const showToast = useAppStore((s) => s.showToast);
  const pins = useSessionPins();
  const [newOpen, setNewOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const familyCounts = useMemo(() => {
    let cc = 0;
    let oc = 0;
    let cx = 0;
    for (const s of sessions) {
      if (s.family === 'claude-code') cc += 1;
      else if (s.family === 'opencode') oc += 1;
      else if (s.family === 'codex') cx += 1;
    }
    return { cc, oc, cx };
  }, [sessions]);

  /**
   * 置顶区摆哪几场。
   *
   * 次序照置顶的次序，不按最后活动时刻重排——那一区的意义正是"我说了算"，跟着活动时刻
   * 重排等于把人刚摆好的次序打乱。名单里有编号、清单里却没有那场（档案被删或被滚删）时
   * 就是不显示，NEVER 因此把编号从名单里踢掉：一次滚删不该悄悄清空人的置顶。
   */
  const pinnedRows = useMemo(() => {
    if (!pins.pinned.length) return [];
    const rank = new Map(pins.pinned.map((id, i) => [id, i]));
    return searched
      .filter((s) => rank.has(s.session_id))
      .sort((a, b) => rank.get(a.session_id)! - rank.get(b.session_id)!);
  }, [searched, pins.pinned]);

  /** 置顶的那几场不在下面再出现一次。同一场摆两处，人会以为是两场。 */
  const restRows = useMemo(
    () => (pins.pinned.length ? visible.filter((s) => !pins.isPinned(s.session_id)) : visible),
    [visible, pins]
  );

  /**
   * 摆进列表的每一行：分区标题与会话卡走同一条队。
   *
   * 分区标题做成**普通一行**而不是窗口化列表的 group header：group header 的位置要等
   * 列表量完每一行的高度才算得出来，量完之前那两行标题一个都不在页面上——真实浏览器里
   * 就撞见过整片清单已经摆好、标题还没出现。标题是折叠开关所在，它不该等任何东西。
   *
   * 一场都没置顶时连标题都不长，整片就是从前那个单列清单——空着的分区标题只是噪音。
   */
  const rows = useMemo<RailRow[]>(() => {
    if (!pins.pinned.length) return restRows.map((session) => ({ kind: 'session' as const, session }));
    return [
      { kind: 'pinned-header' as const },
      ...(pins.collapsed
        ? []
        : pinnedRows.map((session) => ({ kind: 'session' as const, session }))),
      { kind: 'rest-header' as const },
      ...restRows.map((session) => ({ kind: 'session' as const, session })),
    ];
  }, [pins.pinned.length, pins.collapsed, pinnedRows, restRows]);

  const handleTogglePin = async (session: WorkbenchSession) => {
    const wasPinned = pins.isPinned(session.session_id);
    try {
      await pins.toggle(session.session_id);
      // 折起来的时候置顶一场，那一场会立刻消失在眼前。说一句它去哪了。
      if (!wasPinned && pins.collapsed) {
        showToast(t('workbench.rail.pinnedToastCollapsed'), 'success');
      }
    } catch (e) {
      showToast(
        e instanceof Error ? e.message : t('workbench.errors.pinSaveFailedPlain'),
        'error'
      );
    }
  };

  const handleCopy = async (session: WorkbenchSession) => {
    try {
      await navigator.clipboard.writeText(resumeCommand(session));
      setCopiedId(session.session_id);
      showToast(t('workbench.rail.copied'), 'success');
      setTimeout(() => setCopiedId((cur) => (cur === session.session_id ? null : cur)), 1500);
    } catch {
      showToast(t('workbench.rail.copyFailed'), 'error');
    }
  };

  return (
    <aside className="flex h-full min-h-0 w-full flex-col border-r border-border-color bg-bg-secondary">
      <div className="shrink-0 space-y-1.5 border-b border-border-color px-2.5 pb-2.5 pt-2.5">
        {/* 新建会话是一行，不是一整块实心色。整条侧栏最抢眼的东西不该是一颗按钮——
            人来这一页是为了找会话，不是为了建会话。 */}
        <button
          type="button"
          onClick={() => setNewOpen(true)}
          data-testid="new-session"
          className="flex h-8 w-full items-center gap-2 rounded-[8px] px-2.5 text-[13px] font-semibold bg-[var(--accent-primary)] text-[var(--text-on-accent)] transition-opacity duration-200 hover:opacity-90"
        >
          <Plus size={16} strokeWidth={1.5} className="shrink-0" />
          <span>{t('workbench.rail.newSession')}</span>
        </button>

        <div className="flex items-center gap-1.5">
          <div className="flex h-8 min-w-0 flex-1 items-center gap-1.5 rounded-[8px] bg-bg-subtle px-2.5 ring-1 ring-inset ring-transparent focus-within:ring-border-strong">
            <Search size={14} strokeWidth={1.5} className="shrink-0 text-text-muted" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('workbench.rail.searchPlaceholder')}
              aria-label={t('workbench.rail.searchLabel')}
              className="w-full min-w-0 bg-transparent text-[13px] text-text-primary outline-none placeholder:text-text-muted"
            />
            {content.searching ? (
              <Loader2 size={13} className="shrink-0 animate-spin text-text-muted" />
            ) : null}
            {search ? (
              <button
                type="button"
                onClick={() => setSearch('')}
                aria-label={t('workbench.rail.clearSearch')}
                className="shrink-0 text-text-muted hover:text-text-primary"
              >
                <X size={13} />
              </button>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => void reload()}
            disabled={loading}
            aria-label={t('workbench.rail.reload')}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] text-text-muted transition-colors duration-200 hover:bg-bg-hover hover:text-text-primary disabled:opacity-50"
          >
            {loading ? (
              <Loader2 size={14} strokeWidth={1.5} className="animate-spin" />
            ) : (
              <RefreshCw size={14} strokeWidth={1.5} />
            )}
          </button>
        </div>

        <div className="flex flex-wrap gap-1">
          {DAY_FILTERS.map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setDays(d)}
              aria-pressed={days === d}
              data-testid={`day-filter-${d}`}
              className={`rounded-[6px] px-2 py-[3px] text-[11px] transition-colors duration-200 ${
                days === d ? CHIP_ON : CHIP_OFF
              }`}
            >
              {d === 0 ? t('workbench.rail.dayAll') : t('workbench.rail.dayRange', { days: d })}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-1">
          {FILTERS.map((id) => (
            <button
              key={id}
              type="button"
              onClick={() => setStatus(id)}
              aria-pressed={status === id}
              data-testid={`status-filter-${id}`}
              className={`flex items-center gap-1.5 rounded-[6px] px-2 py-[3px] text-[11px] transition-colors duration-200 ${
                status === id ? CHIP_ON : CHIP_OFF
              }`}
            >
              {/* 点保留各档的语义色：那是数据，不是操作面。 */}
              {id === 'all' ? null : <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[id]}`} />}
              <span>{t(FILTER_LABEL_KEY[id])}</span>
              <span className="font-mono opacity-60">{counts[id]}</span>
            </button>
          ))}
        </div>

        {/* 内容检索比敲字慢一拍，所以它自己报进度。没搜到就明说没搜到，NEVER 让人
            对着一份只按标题筛出来的清单以为"内容里也没有"。 */}
        {search.trim().length >= MIN_CONTENT_QUERY ? (
          <p data-testid="content-search-status" className="text-[11px] text-text-muted">
            {content.error
              ? content.error
              : content.searching
                ? t('workbench.rail.contentSearching')
                : t('workbench.rail.contentHits', { n: content.matches.size })}
          </p>
        ) : null}
        {content.warnings.map((warning) => (
          <p key={warning} className="text-[11px] text-text-secondary">
            {warning}
          </p>
        ))}
      </div>

      {/* 正在起的那一场先占一行。它摆在滚动区**外面**：这一行的意义是"你刚建的那场在
          这儿"，滚下去看不见就等于没有。会话真进了清单它自己就消失，位置随即让给真那一行。 */}
      {launch ? (
        <div className="shrink-0 px-2 pt-2">
          <div
            data-testid="rail-launch"
            data-phase={launch.phase}
            className={`flex items-center gap-2 rounded-[8px] border px-2.5 py-2 ${
              launch.phase === 'failed'
                ? 'border-accent-error bg-accent-error-10'
                : 'border-border-accent bg-accent-primary-10'
            }`}
          >
            <Mail
              size={14}
              strokeWidth={2}
              className={`shrink-0 ${
                launch.phase === 'failed' ? 'text-accent-error' : 'text-accent-primary'
              }`}
            />
            <div className="flex min-w-0 flex-1 flex-col">
              <span className="truncate text-[12px] font-medium text-text-primary">
                {launch.text || t('workbench.launch.railTitle')}
              </span>
              <span className="truncate text-[11px] text-text-muted">
                {launch.phase === 'failed'
                  ? t('workbench.launch.railFailed')
                  : launch.phase === 'claiming'
                    ? t('workbench.launch.railClaiming', { name: launch.agentName })
                    : t('workbench.launch.railWarming', { name: launch.agentName })}
              </span>
            </div>
            {launch.phase === 'failed' ? (
              <button
                type="button"
                data-testid="rail-launch-dismiss"
                onClick={() => onDismissLaunch?.()}
                aria-label={t('workbench.launch.dismiss')}
                className="shrink-0 rounded-[6px] p-0.5 text-text-muted hover:text-text-primary"
              >
                <X size={13} />
              </button>
            ) : (
              <Loader2 size={13} className="shrink-0 animate-spin text-accent-primary" />
            )}
          </div>
        </div>
      ) : null}

      {/* 列表区：Virtuoso 只渲染视口内卡片。装载时给骨架屏占位，有数据才展示窗口化列表。 */}
      <div className="min-h-0 flex-1">
        {/* 报错摆在清单**上面**而不是替掉清单：定时重取偶尔失手时，手上那份清单仍
            比一句错误有用得多。 */}
        {error && (
          <p className="m-3 rounded-[6px] bg-bg-subtle px-2.5 py-2 text-[12px] text-text-secondary">
            {error}
          </p>
        )}
        {loading && !visible.length ? (
          <div className="animate-pulse px-2 pt-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="mb-0.5 w-full rounded-[8px] px-2.5 py-2">
                <div className="mb-2 h-3.5 w-2/3 rounded bg-bg-hover" />
                <div className="h-2.5 w-1/2 rounded bg-bg-hover" />
              </div>
            ))}
          </div>
        ) : !rows.length ? (
          <p className="px-3 py-8 text-center text-[12px] text-text-muted">
            {t('workbench.rail.empty')}
          </p>
        ) : (
          /* 置顶区与其余那一片共用同一条队、同一条滚动条。两个列表并排摆的话，置顶那一片
             要么自己不窗口化（置顶数不设上限，迟早卡），要么各滚各的（两条滚动条挨着，
             没人分得清该滚哪条）。 */
          <Virtuoso
            data={rows}
            initialItemCount={Math.min(rows.length, 30)}
            /* 滚动容器的内容不许贴着容器上下沿。顶上 8px 让第一张卡与筛选区之间有
               一道呼吸，底下 16px 让最后一张滚到底时不是被硬切在边框上。 */
            components={{
              Header: () => <div className="h-2" />,
              Footer: () => <div className="h-4" />,
            }}
            computeItemKey={(_, row) =>
              row.kind === 'session' ? row.session.session_id : row.kind
            }
            itemContent={(_, row) => {
              if (row.kind === 'pinned-header') {
                return (
                  <button
                    type="button"
                    onClick={() => pins.setCollapsed(!pins.collapsed)}
                    aria-expanded={!pins.collapsed}
                    data-testid="pinned-header"
                    className="flex w-full items-center gap-1.5 px-2.5 pb-1 pt-2 text-[11px] font-medium uppercase tracking-wide text-text-muted transition-colors duration-200 hover:text-text-secondary"
                  >
                    {pins.collapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}
                    <Pin size={11} fill="currentColor" className={ACCENT_TEXT} />
                    <span className={ACCENT_TEXT}>{t('workbench.rail.pinnedHeader')}</span>
                    {/* 折起来时这个数就是全部线索：不报的话，人看不出自己折掉了什么。 */}
                    <span className="font-mono opacity-70">{pinnedRows.length}</span>
                  </button>
                );
              }
              if (row.kind === 'rest-header') {
                return (
                  <div
                    data-testid="rest-header"
                    className="px-2.5 pb-1 pt-3 text-[11px] font-medium uppercase tracking-wide text-text-muted"
                  >
                    {t('workbench.rail.restHeader')}{' '}
                    <span className="font-mono opacity-70">{restRows.length}</span>
                  </div>
                );
              }
              const session = row.session;
              return (
                <div className="px-2">
                  <SessionItem
                    session={session}
                    selected={session.session_id === selectedId}
                    copied={copiedId === session.session_id}
                    pinned={pins.isPinned(session.session_id)}
                    contentMatch={content.matches.get(session.session_id) ?? null}
                    onSelect={onSelect}
                    onCopy={handleCopy}
                    onTogglePin={handleTogglePin}
                  />
                  {/* 行与行之间的间隔。连同每行自己的 py-2，行间总共留出 24px，
                      而行内最大的间距是 4px——差出六倍，清单才读得出是一行一行的。 */}
                  <div className="h-2" />
                </div>
              );
            }}
          />
        )}
      </div>

      <div className="shrink-0 border-t border-border-color px-2.5 py-2 font-mono text-[11px] leading-[1.6] text-text-muted">
        {t('workbench.rail.summary', {
          total: sessions.length,
          cc: familyCounts.cc,
          oc: familyCounts.oc,
          cx: familyCounts.cx,
        })}
      </div>

      {/* 建完就交出去。等编号、反复重取清单、把中栏切过去，这些事由页面那边的启动状态
          统一管（见 `useSessionLaunch`）——左栏自己等的话，那段等待只有左栏知道，中栏
          仍是一片空白，而人点完创建看的正是中栏。 */}
      <NewSessionModal
        isOpen={newOpen}
        onClose={() => setNewOpen(false)}
        onCreated={(pending, text) => onCreated?.(pending, text)}
      />
    </aside>
  );
}
