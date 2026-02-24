/**
 * API 错误提取工具函数
 */
import { AxiosError } from 'axios';

/**
 * 从 API 错误中提取用户友好的错误消息
 */
export function extractApiError(err: unknown, defaultMsg: string = '操作失败，请稍后重试'): string {
    if (!(err instanceof AxiosError)) {
        return '网络错误，请检查网络连接';
    }
    const status = err.response?.status;
    const detail = err.response?.data?.detail;

    if (status === 429) {
        return '请求过于频繁，请稍后再试';
    }
    if (status === 402 && detail) {
        if (typeof detail === 'object') {
            return `积分不足：需要 ${detail.required} 积分，当前余额 ${detail.current}`;
        }
        return String(detail);
    }
    if (typeof detail === 'string') {
        return detail;
    }
    if (detail?.detail && typeof detail.detail === 'string') {
        return detail.detail;
    }
    return defaultMsg;
}
