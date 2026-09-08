/**
 * useAttachments — 「人手上这几个文件，先收着，等会儿一起发出去」。
 *
 * 收文件这件事在页面上有两处：中栏输入区（对着一场已有的会话说话）和新建会话对话框
 * （第一句话）。两处收的是同一种东西、分的是同一条界（图片走"打开看"、文档走"打开
 * 读"）、受同一个数量上限，所以判据只写这一份。各写一份的话，粘贴一张 PNG 在一处是
 * 缩略图、在另一处成了一行文件名，而没有人会觉得那是同一个功能。
 *
 * **浏览器读不到本机文件的真实路径**，那是它的安全边界，选文件拿不到、拖拽也拿不到。
 * 所以两处都只能走"内容以 base64 交上去、服务端落盘、把服务端那一侧的绝对路径拼进
 * 提示词"这一条路——agent 拿到的是一条它真的打得开的路径。
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import i18n from '@/i18n';

/** 一次最多附几个。与服务端 `webui_uploads._MAX_COUNT` 对齐，超出的丢弃。 */
export const MAX_ATTACHMENTS = 8;

/** 一张已附加、待发送的图片。`dataUrl` 原样发给服务端，`name` 供缩略图的替代文字。 */
export interface AttachedImage {
  id: string;
  /** `data:image/...;base64,....` */
  dataUrl: string;
  name: string;
}

/**
 * 一份已附加、待发送的文档。
 *
 * `name` 不只是显示用：服务端拿它给落盘文件起名，agent 在提示词里看到的路径末尾就是
 * 这个名字，它靠这个名字（尤其是扩展名）判断该怎么读。
 */
export interface AttachedDoc {
  id: string;
  /** `data:<mime>;base64,....` */
  dataUrl: string;
  name: string;
  /** 字节数，界面上报给人看。 */
  size: number;
}

export interface AttachmentsState {
  images: AttachedImage[];
  documents: AttachedDoc[];
  /** 收文件（选择、粘贴、拖入三条路共用）。按 MIME 分给图片或文档两条路。 */
  addFiles: (files: FileList | File[]) => Promise<void>;
  removeImage: (id: string) => void;
  removeDocument: (id: string) => void;
  /** 整份清空（换会话、发出去了、对话框重开）。 */
  clear: () => void;
  /** 原样放回去（发失败退单）。 */
  restore: (images: AttachedImage[], documents: AttachedDoc[]) => void;
  /** 图片加文档共几个。闸「还能不能再附」用的就是它。 */
  count: number;
}

export function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () =>
      reject(reader.error ?? new Error(i18n.t('workbench.errors.imageUnreadable')));
    reader.readAsDataURL(file);
  });
}

export function useAttachments(): AttachmentsState {
  const [images, setImages] = useState<AttachedImage[]>([]);
  const [documents, setDocuments] = useState<AttachedDoc[]>([]);
  // 编号用单调自增，不掺时间戳与随机数——同一毫秒连附两张会撞。
  const counter = useRef(0);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  /**
   * 收下一批文件，按 MIME 分成图片与文档两路。
   *
   * 分两路不是为了好看：图片在界面上是缩略图、在提示词里是"打开看"，文档在界面上是
   * 一行文件名、在提示词里是"打开读"。合成一路的话，两种都会被当成其中一种处理。
   *
   * 判据取浏览器给的 MIME 而不是扩展名——扩展名是可以骗人的，而这里分错的后果是
   * 一份 PDF 被当成图片送去"看图"。MIME 认不出来（有些系统对 `.md` 就报空）时按文档
   * 处理：文档那条路对内容不做任何假设，是安全的那一档。
   */
  const addFiles = useCallback(async (files: FileList | File[]) => {
    const all = Array.from(files);
    if (all.length === 0) return;
    const pics = all.filter((f) => f.type.startsWith('image/'));
    const docs = all.filter((f) => !f.type.startsWith('image/'));

    if (pics.length) {
      const read = await Promise.all(
        pics.map(async (f) => ({
          id: `img-${counter.current++}`,
          dataUrl: await readFileAsDataUrl(f),
          name: f.name || 'image',
        }))
      );
      if (!mounted.current) return;
      setImages((cur) => [...cur, ...read].slice(0, MAX_ATTACHMENTS));
    }

    if (docs.length) {
      const read = await Promise.all(
        docs.map(async (f) => ({
          id: `doc-${counter.current++}`,
          dataUrl: await readFileAsDataUrl(f),
          name: f.name || 'file',
          size: f.size,
        }))
      );
      if (!mounted.current) return;
      setDocuments((cur) => [...cur, ...read].slice(0, MAX_ATTACHMENTS));
    }
  }, []);

  const removeImage = useCallback((id: string) => {
    setImages((cur) => cur.filter((im) => im.id !== id));
  }, []);

  const removeDocument = useCallback((id: string) => {
    setDocuments((cur) => cur.filter((d) => d.id !== id));
  }, []);

  const clear = useCallback(() => {
    setImages([]);
    setDocuments([]);
  }, []);

  const restore = useCallback((nextImages: AttachedImage[], nextDocs: AttachedDoc[]) => {
    setImages(nextImages);
    setDocuments(nextDocs);
  }, []);

  return {
    images,
    documents,
    addFiles,
    removeImage,
    removeDocument,
    clear,
    restore,
    count: images.length + documents.length,
  };
}
