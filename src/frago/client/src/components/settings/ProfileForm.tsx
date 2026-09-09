import { Eye, EyeOff } from 'lucide-react';
import type { ProfilesController } from './useProfiles';

export default function ProfileForm({ pm }: { pm: ProfilesController }) {
  const {
    t,
    presets,
    vendorCores,
    viewMode,
    formName,
    setFormName,
    formKind,
    setFormKind,
    formAgentType,
    setFormAgentType,
    formEndpointType,
    setFormEndpointType,
    formApiKey,
    setFormApiKey,
    formUrl,
    setFormUrl,
    formDefaultModel,
    setFormDefaultModel,
    formSonnetModel,
    setFormSonnetModel,
    formHaikuModel,
    setFormHaikuModel,
    showFormApiKey,
    setShowFormApiKey,
    formSubmitting,
    setViewMode,
    resetForm,
    handleFormSubmit,
  } = pm;

  // A preset already knows its URL and its models. Showing them as the field's
  // placeholder is what turns "Default Model" from a field you have to look up
  // elsewhere into one you can leave alone unless you mean to override it.
  const preset = presets.find((p) => p.id === formEndpointType);

  // A vendor CLI is a different set of questions, not a variant of the same
  // ones: no endpoint to reach, no key to hold, and a model list that comes
  // from that CLI's own service rather than from a preset table.
  const isVendorCli = formKind === 'vendor_cli';
  const core = vendorCores.find((c) => c.agent_type === formAgentType);

  return (
    <div className="space-y-3">
      {/* Profile name */}
      <div>
        <label htmlFor="profile-name" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
          {t('settings.profiles.profileName')}
        </label>
        <input
          id="profile-name"
          type="text"
          value={formName}
          onChange={(e) => setFormName(e.target.value)}
          placeholder={t('settings.profiles.profileNamePlaceholder')}
          className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
          autoFocus
        />
      </div>

      {/* What kind of connection this is. Hidden when frago knows of no core
          that runs on its own account — a picker with one option is noise. */}
      {vendorCores.length > 0 && (
        <div>
          <label htmlFor="profile-kind" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
            {t('settings.profiles.connectionKind')}
          </label>
          <select
            id="profile-kind"
            value={formKind}
            onChange={(e) => {
              const kind = e.target.value as typeof formKind;
              setFormKind(kind);
              // Land on a usable core straight away; an empty core is the one
              // thing the backend will refuse to save.
              if (kind === 'vendor_cli' && !formAgentType) {
                setFormAgentType(vendorCores[0].agent_type);
              }
            }}
            className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
          >
            <option value="endpoint">{t('settings.profiles.kindEndpoint')}</option>
            <option value="vendor_cli">{t('settings.profiles.kindVendorCli')}</option>
          </select>
          {isVendorCli && (
            <p className="text-xs text-[var(--text-muted)] mt-1">
              {t('settings.profiles.vendorCliHint')}
            </p>
          )}
        </div>
      )}

      {isVendorCli ? (
        <>
          {/* Which core, and which of the models its own service offers. */}
          <div>
            <label htmlFor="profile-agent-core" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
              {t('settings.profiles.agentCore')}
            </label>
            <select
              id="profile-agent-core"
              value={formAgentType}
              onChange={(e) => setFormAgentType(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
            >
              {vendorCores.map((c) => (
                <option key={c.agent_type} value={c.agent_type}>
                  {c.display_name}
                  {c.installed ? '' : ` — ${t('settings.profiles.notInstalled')}`}
                </option>
              ))}
            </select>
            {core?.reason && (
              <p className="text-xs text-[var(--text-muted)] mt-1">{core.reason}</p>
            )}
          </div>

          <div>
            <label htmlFor="profile-vendor-model" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
              {t('settings.profiles.defaultModel')}
            </label>
            {/* A datalist rather than a plain select: the roster is what this
                CLI offered when frago last looked, and it moves. Typing a name
                that is not on it has to keep working. */}
            <input
              id="profile-vendor-model"
              type="text"
              list="profile-vendor-model-options"
              value={formDefaultModel}
              onChange={(e) => setFormDefaultModel(e.target.value)}
              placeholder={core?.known_models[0] ?? ''}
              className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] font-mono"
            />
            <datalist id="profile-vendor-model-options">
              {(core?.known_models ?? []).map((m) => (
                <option key={m} value={m} />
              ))}
            </datalist>
            {core && core.known_models.length > 0 && (
              <p className="text-xs text-[var(--text-muted)] mt-1">
                {t('settings.profiles.modelCandidates')}: {core.known_models.join(', ')}
              </p>
            )}
          </div>
        </>
      ) : (
        <>
      {/* Endpoint type */}
      <div>
        <label htmlFor="profile-endpoint-type" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
          {t('settings.profiles.endpointType')}
        </label>
        <select
          id="profile-endpoint-type"
          value={formEndpointType}
          onChange={(e) => setFormEndpointType(e.target.value)}
          className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
        >
          {presets.map((p) => (
            <option key={p.id} value={p.id}>
              {p.display_name}
            </option>
          ))}
          <option value="custom">{t('settings.profiles.customEndpoint')}</option>
        </select>
      </div>

      {/* Where requests will actually go. A custom endpoint has to be told;
          a preset already knows, and says so instead of staying silent. */}
      {formEndpointType === 'custom' ? (
        <div>
          <label htmlFor="profile-url" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
            {t('settings.profiles.apiUrl')}
          </label>
          <input
            id="profile-url"
            type="text"
            value={formUrl}
            onChange={(e) => setFormUrl(e.target.value)}
            placeholder="https://api.example.com/anthropic"
            className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] font-mono"
          />
        </div>
      ) : (
        preset && (
          <p className="text-xs text-[var(--text-muted)] font-mono break-all">
            {preset.base_url}
          </p>
        )
      )}

      {/* API Key */}
      <div>
        <label htmlFor="profile-api-key" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
          {t('settings.profiles.apiKey')}
          {viewMode === 'edit' && (
            <span className="ml-2 text-[var(--text-muted)]">({t('settings.general.leaveEmptyToKeep')})</span>
          )}
        </label>
        <div className="flex gap-2">
          <input
            id="profile-api-key"
            type={showFormApiKey ? 'text' : 'password'}
            value={formApiKey}
            onChange={(e) => setFormApiKey(e.target.value)}
            placeholder={viewMode === 'edit' ? t('settings.general.leaveEmptyToKeep') : t('settings.general.enterApiKey')}
            className="flex-1 px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] font-mono"
          />
          <button
            type="button"
            onClick={() => setShowFormApiKey(!showFormApiKey)}
            className="btn btn-ghost btn-sm p-2"
            aria-label={showFormApiKey ? t('settings.general.hideApiKey') : t('settings.general.showApiKey')}
          >
            {showFormApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
      </div>

      {/* Model overrides. Left empty, a preset uses the model in its
          placeholder; a custom endpoint has nothing to fall back on. */}
      <div>
        <label htmlFor="profile-default-model" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
          {t('settings.profiles.defaultModel')}
          {preset && <span className="ml-1 text-[var(--text-muted)]">- {t('settings.general.optionalOverride')}</span>}
        </label>
        <input
          id="profile-default-model"
          type="text"
          value={formDefaultModel}
          onChange={(e) => setFormDefaultModel(e.target.value)}
          placeholder={preset ? preset.default_model : 'e.g., gpt-4'}
          className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] font-mono"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="profile-sonnet-model" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
            {t('settings.profiles.sonnetModel')}
          </label>
          <input
            id="profile-sonnet-model"
            type="text"
            value={formSonnetModel}
            onChange={(e) => setFormSonnetModel(e.target.value)}
            placeholder={preset ? preset.sonnet_model : t('settings.general.optionalOverride')}
            className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] font-mono"
          />
        </div>
        <div>
          <label htmlFor="profile-haiku-model" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
            {t('settings.profiles.haikuModel')}
          </label>
          <input
            id="profile-haiku-model"
            type="text"
            value={formHaikuModel}
            onChange={(e) => setFormHaikuModel(e.target.value)}
            placeholder={preset ? preset.haiku_model : t('settings.general.optionalOverride')}
            className="w-full px-3 py-2 text-sm bg-[var(--bg-base)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] font-mono"
          />
        </div>
      </div>
        </>
      )}

      {/* Form actions */}
      <div className="flex gap-2 pt-2">
        <button
          type="button"
          onClick={handleFormSubmit}
          disabled={formSubmitting || !formName.trim()}
          className="btn btn-primary btn-sm disabled:opacity-50"
        >
          {formSubmitting
            ? viewMode === 'add'
              ? t('settings.profiles.creating')
              : t('settings.profiles.updating')
            : t('settings.profiles.save')}
        </button>
        <button
          type="button"
          onClick={() => {
            setViewMode('list');
            resetForm();
          }}
          className="btn btn-ghost btn-sm"
        >
          {t('settings.profiles.cancel')}
        </button>
      </div>
    </div>
  );
}
