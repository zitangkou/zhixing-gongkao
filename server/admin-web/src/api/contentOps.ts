import http, { getData } from './http'

export type ContentOpsStatus = 'draft' | 'teaching_review' | 'ops_review' | 'ready' | 'published' | 'rejected'
export interface ContentOpsTemplate { id: string; code: string; productKey: string; name: string; description: string; slots: string[]; channels: string[]; sortOrder: number; status: string }
export interface ContentVariant { title?: string; body?: string; [key: string]: unknown }
export interface ContentPackage { id: string; productKey: string; templateId: string; sourceType: string; sourceId: string; sourceTitle: string; campaignKey: string; deepLink: string; slotValues: Record<string, string>; variants: Record<string, ContentVariant>; reviewNote: string; status: ContentOpsStatus; plannedAt?: string; publishedAt?: string; createdAt: string; updatedAt: string }
export interface ContentPackageExport { schemaVersion: string; generatedAt: string; template: ContentOpsTemplate; package: ContentPackage; channels: Array<{ channel: string; content: ContentVariant; deepLink: string; plannedAt?: string; manualPublishRequired: boolean }>; checklist: string[] }

export const fetchContentTemplates = (productKey?: string) => getData<ContentOpsTemplate[]>(http.get('/admin/content-ops/templates', { params: { productKey } }))
export const fetchContentPackages = (params?: { productKey?: string; status?: string }) => getData<ContentPackage[]>(http.get('/admin/content-ops/packages', { params }))
export const createContentPackage = (data: Record<string, unknown>) => getData<ContentPackage>(http.post('/admin/content-ops/packages', data))
export const updateContentPackage = (id: string, data: Record<string, unknown>) => getData<ContentPackage>(http.put(`/admin/content-ops/packages/${id}`, data))
export const updateContentPackageStatus = (id: string, status: ContentOpsStatus, reviewNote = '') => getData<ContentPackage>(http.post(`/admin/content-ops/packages/${id}/status`, { status, reviewNote }))
export const exportContentPackage = (id: string) => getData<ContentPackageExport>(http.get(`/admin/content-ops/packages/${id}/export`))
