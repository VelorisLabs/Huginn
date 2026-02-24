/**
 * PDF 工具函数
 */

/**
 * 通过 API 加载论文 PDF 并在新标签页打开
 */
export async function openPdfInNewTab(paperId: number): Promise<void> {
    const token = localStorage.getItem('access_token') || '';
    const res = await fetch(`/api/v1/papers/${paperId}/pdf-data?token=${encodeURIComponent(token)}`);
    if (!res.ok) throw new Error('PDF 加载失败');
    const json = await res.json();
    const byteChars = atob(json.data);
    const byteArray = new Uint8Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
        byteArray[i] = byteChars.charCodeAt(i);
    }
    const blob = new Blob([byteArray], { type: 'application/pdf' });
    window.open(URL.createObjectURL(blob), '_blank');
}
