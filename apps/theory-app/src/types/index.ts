export interface MindMapNode {
  id: string
  title: string
  content?: string
  children?: MindMapNode[]
}

export interface ArticleSection {
  id: string
  title: string
  level: 1 | 2 | 3
  content?: string
  highlight?: string
  children?: ArticleSection[]
}

export interface Article {
  id: string
  title: string
  source: string
  publishDate: string
  summary: string
  sections: ArticleSection[]
  content: string
  tags: string[]
  mindMap: MindMapNode
}

export interface KnowledgeNode {
  id: string
  treeKey: string
  parentId: string | null
  title: string
  content: string
  myNote: string
  isStarred: boolean
  depth: number
  sortOrder: number
  path: string
  sourceFile?: string
  children: KnowledgeNode[] | null
}

export interface KnowledgeTree {
  treeKey: string
  title: string
  nodes: KnowledgeNode[]
}

export interface CorpusItem {
  id: string
  original: string
  kind: string
  sourceType: string
  sourceTitle: string
  tags: string[]
  plainNote: string
  rewrite: string
  practice: string
  status: string
  usedCount: number
  promotedTermId: string | null
  knowledgeNodeId?: string | null
  knowledgeTreeKey?: string
  knowledgePath?: string
  createdAt: string
  updatedAt: string
}

export interface CorpusStats {
  inboxCount: number
  clarifiedCount: number
  ownedCount: number
  usedCount: number
  total: number
  kinds: string[]
  sourceTypes: string[]
  tagPresets: string[]
}
