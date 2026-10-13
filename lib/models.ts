export interface Paper { id:string; title:string; authors:string[]; journal:string|null; year:number|null; abstract:string|null; doi:string|null; citations:number|null; openAccess:boolean|null; type:string; provider:'OpenAlex'|'Crossref'|'Demo'; url:string|null; fullTextUrl:string|null; demo:boolean; score?:number; matchedTerms?:string[] }
export interface Project { id:string; title:string; question:string; framework:string; demo:boolean; createdAt:string }
export interface SavedPaper { paper:Paper; projectId:string; status:'Unread'|'Reading'|'Completed'; collection:string; notes:string; favorite:boolean }
export interface WorkspaceData { projects:Project[]; saved:SavedPaper[] }
export type View='home'|'search'|'projects'|'library'|'settings'|'roadmap';
export interface SourceEvidence { paperId:string; page:number|null; section:string|null; quote:string; verified:boolean }
export interface ExtractedValue { id:string; paperId:string; field:string; value:string|number|null; evidence:SourceEvidence; origin:'source'|'user'|'ai'; verified:boolean }
export interface EffectEstimate { studyId:string; effect:number; standardError:number; measure:'logOR'|'logRR'|'MD'|'SMD'|'logHR' }
