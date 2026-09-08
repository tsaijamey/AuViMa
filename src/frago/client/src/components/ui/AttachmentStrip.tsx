/**
 * AttachmentStrip — 「等会儿要一起发出去的这几个文件」摆在人眼前的那一条。
 *
 * 图片与文档摆法不同，因为要人确认的东西不同：
 *
 * - 图片给缩略图。人粘进来的常常是连着截的好几张，只有看见画面才分得清刚才那张是哪张。
 * - 文档不给缩略图——一份 PDF 的首页缩成 64px 什么也看不出来。它要的是名字（尤其扩展名，
 *   agent 靠它判断怎么读）和大小。
 *
 * 每一个都能单独撤掉：粘错一张就得能只把那张拿走，而不是整批清空重来。
 *
 * `idPrefix` 只影响 `data-testid`，不影响样子。中栏输入区与新建会话对话框共用这一条，
 * 两处的测试各认各的名字。
 */

import { useTranslation } from 'react-i18next';
import { FileText, X } from 'lucide-react';
import type { AttachedDoc, AttachedImage } from '@/hooks/useAttachments';

export interface AttachmentStripProps {
  images: AttachedImage[];
  documents: AttachedDoc[];
  onRemoveImage: (id: string) => void;
  onRemoveDocument: (id: string) => void;
  /** `data-testid` 的前缀，如 `composer` → `composer-thumb`。 */
  idPrefix: string;
}

/** 字节数 → 人话。只报已经发生的量，没有分母。 */
export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function AttachmentStrip({
  images,
  documents,
  onRemoveImage,
  onRemoveDocument,
  idPrefix,
}: AttachmentStripProps) {
  const { t } = useTranslation();
  if (!images.length && !documents.length) return null;

  return (
    <>
      {images.length ? (
        <div className="flex flex-wrap gap-2">
          {images.map((image) => (
            <div
              key={image.id}
              data-testid={`${idPrefix}-thumb`}
              className="relative h-16 w-16 overflow-hidden rounded-[8px] border border-border-color bg-bg-subtle"
            >
              <img src={image.dataUrl} alt={image.name} className="h-full w-full object-cover" />
              <button
                type="button"
                data-testid={`${idPrefix}-remove`}
                aria-label={t('workbench.composer.removeImage', { name: image.name })}
                onClick={() => onRemoveImage(image.id)}
                className="absolute right-[2px] top-[2px] rounded-full bg-bg-card/90 p-[2px] text-text-secondary hover:text-text-primary"
              >
                <X size={11} />
              </button>
            </div>
          ))}
        </div>
      ) : null}

      {documents.length ? (
        <div className="flex flex-wrap gap-1.5">
          {documents.map((doc) => (
            <span
              key={doc.id}
              data-testid={`${idPrefix}-doc`}
              className="flex max-w-full items-center gap-1.5 rounded-[8px] border border-border-color bg-bg-subtle py-1 pl-2 pr-1 text-[12px] text-text-secondary"
            >
              <FileText size={13} strokeWidth={1.5} className="shrink-0 text-text-muted" />
              <span className="min-w-0 truncate">{doc.name}</span>
              <span className="shrink-0 font-mono text-[11px] text-text-dim">
                {formatSize(doc.size)}
              </span>
              <button
                type="button"
                data-testid={`${idPrefix}-doc-remove`}
                aria-label={t('workbench.composer.removeFile', { name: doc.name })}
                onClick={() => onRemoveDocument(doc.id)}
                className="shrink-0 rounded-[4px] p-0.5 text-text-muted hover:text-text-primary"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
      ) : null}
    </>
  );
}
