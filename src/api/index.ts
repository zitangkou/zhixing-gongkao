/* API 聚合入口：按域拆分后统一导出 api 对象，保持调用方兼容。 */
import { apiAuth } from './domains/auth'
import { apiExam } from './domains/exam'
import { apiKnowledge } from './domains/knowledge'
import { apiLearning } from './domains/learning'
import { apiManualWrong } from './domains/manualWrong'
import { apiPersonal } from './domains/personal'
import { apiPlan } from './domains/plan'
import { apiRmrb } from './domains/rmrb'
import { apiZiliao } from './domains/ziliao'
export { isMock, initUserFromMock } from './_shared'
export type { AuthResult, UserMeData } from './_shared'

export const api = {
  ...apiAuth,
  ...apiLearning,
  ...apiPlan,
  ...apiKnowledge,
  ...apiManualWrong,
  ...apiExam,
  ...apiRmrb,
  ...apiPersonal,
  ...apiZiliao,
}
