/**
 * Connection Roles Card
 *
 * Which connection each role runs on. Two rows, because the two roles are
 * genuinely different acts and the card that came before this one showed only
 * the first: binding the main agent writes the connection into each agent
 * CLI's own configuration, while binding the worker is read at launch and
 * written nowhere. Showing them side by side is what makes "my agent stays on
 * my subscription, my workers run somewhere else" a thing you can see rather
 * than a thing you have to remember.
 *
 * The subscription is always the first option and is never absent — it is the
 * state everything starts in and falls back to.
 *
 * Visually this is an ordinary settings row and deliberately nothing more: the
 * label and its explanation on the left, the picker on the right, the same
 * shape the language row and the capability switches already use. Three of this
 * page's standing rules bear on it — colour is reserved for states that need
 * someone to act (two connections sitting where they were put need nobody, so
 * neither row is tinted), every colour goes through a theme variable so the
 * light theme comes out right without a line of its own, and controls copy the
 * class list of the control they resemble rather than inventing one. The first
 * version of this card broke all three: two green dots for two ordinary rows,
 * a colour variable that does not exist, and a class name for a component the
 * stylesheet never defined, which is why the picker rendered as a bare
 * browser-default dropdown.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Layers } from 'lucide-react';
import { bindRole } from '@/api';
import type { ConnectionRole, ProfileItem, RoleBinding } from '@/api';

interface ConnectionRolesCardProps {
  connections: ProfileItem[];
  bindings: RoleBinding[];
  /** agent_type → display name, so the rows read "CodeBuddy Code", not "codebuddy". */
  coreNames: Record<string, string>;
  onManageProfiles: () => void;
  /** Reload after a binding lands: both rows and the cards below read this data. */
  onBindingChanged: () => void;
}

const ROLE_ORDER: ConnectionRole[] = ['main', 'worker'];

export default function ConnectionRolesCard({
  connections,
  bindings,
  coreNames,
  onManageProfiles,
  onBindingChanged,
}: ConnectionRolesCardProps) {
  const { t } = useTranslation();
  const [busyRole, setBusyRole] = useState<ConnectionRole | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleBind = async (role: ConnectionRole, profileId: string) => {
    setBusyRole(role);
    setError(null);
    try {
      const result = await bindRole(role, profileId);
      if (result.status === 'ok') {
        onBindingChanged();
      } else {
        // The backend's refusals are written to be read (a vendor CLI on main
        // says why it cannot go there), so they are shown as-is.
        setError(result.error || t('settings.connections.bindFailed'));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('settings.connections.bindFailed'));
    } finally {
      setBusyRole(null);
    }
  };

  const label = (connection: ProfileItem) => {
    if (connection.kind === 'official') return t('settings.connections.officialName');
    const core = connection.agent_type ? coreNames[connection.agent_type] ?? connection.agent_type : null;
    return core ? `${connection.name} · ${core}` : connection.name;
  };

  /** What this row is running on, in one line under the picker. */
  const detail = (binding: RoleBinding) => {
    const { connection } = binding;
    if (binding.role === 'main' && binding.targets.length > 0) {
      const names = binding.targets.map((target) => coreNames[target] ?? target).join(', ');
      return `${t('settings.connections.writtenInto')}: ${names}`;
    }
    if (connection.agent_type) {
      const core = coreNames[connection.agent_type] ?? connection.agent_type;
      return connection.default_model
        ? `${connection.default_model} ${t('settings.connections.onCore')} ${core}`
        : core;
    }
    return connection.default_model ?? null;
  };

  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border-color)] p-4">
      <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
        {t('settings.connections.title')}
      </h3>

      {/* One row per role: what it is on the left, the picker on the right —
          the shape every other settings row on this page already has. Nothing
          here carries an accent colour: both rows are simply the state things
          are in, and the page reserves colour for the states that need someone
          to act. */}
      <div className="mb-4">
        {ROLE_ORDER.map((role, index) => {
          const binding = bindings.find((b) => b.role === role);
          if (!binding) return null;
          const rowDetail = detail(binding);
          const roleName =
            role === 'main'
              ? t('settings.connections.mainRole')
              : t('settings.connections.workerRole');

          return (
            <div
              key={role}
              className={`flex items-center justify-between gap-4 py-2 ${
                index > 0 ? 'border-t border-[var(--border-color)] pt-3 mt-1' : ''
              }`}
            >
              <div className="min-w-0">
                <div className="text-sm text-[var(--text-primary)]">{roleName}</div>
                <div className="text-xs text-[var(--text-secondary)] mt-0.5">
                  {role === 'main'
                    ? t('settings.connections.mainRoleHint')
                    : t('settings.connections.workerRoleHint')}
                </div>
                {rowDetail && (
                  <div className="text-xs text-[var(--text-muted)] mt-0.5">{rowDetail}</div>
                )}
                {busyRole === role && (
                  <div className="text-xs text-[var(--text-muted)] mt-0.5">
                    {t('settings.connections.switching')}
                  </div>
                )}
              </div>
              <select
                className="shrink-0 max-w-[50%] px-3 py-1.5 rounded-md bg-[var(--bg-subtle)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                value={binding.profile_id ?? 'official'}
                disabled={busyRole !== null}
                onChange={(e) => handleBind(role, e.target.value)}
                aria-label={roleName}
              >
                {connections.map((connection) => {
                  // A vendor CLI cannot serve the main role: frago holds no
                  // key to write into another CLI's config for it. Listed and
                  // disabled with the reason — an option that is simply gone
                  // reads as a bug.
                  const blocked = role === 'main' && connection.kind === 'vendor_cli';
                  return (
                    <option key={connection.id} value={connection.id} disabled={blocked}>
                      {label(connection)}
                      {blocked ? ` — ${t('settings.connections.vendorNotForMain')}` : ''}
                    </option>
                  );
                })}
              </select>
            </div>
          );
        })}
      </div>

      {error && (
        <p className="text-xs text-[var(--accent-error)] mb-3">{error}</p>
      )}

      <button
        type="button"
        onClick={onManageProfiles}
        className="btn btn-ghost btn-sm flex items-center gap-1"
      >
        <Layers size={16} />
        {t('settings.general.manageProfiles')}
      </button>
    </div>
  );
}
