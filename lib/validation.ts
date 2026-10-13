import {z} from 'zod';
const webUrl=z.string().url().max(2000).refine(s=>/^https?:\/\//i.test(s)).nullable();
export const paperSchema=z.object({id:z.string().min(1).max(500),title:z.string().min(1).max(3000),authors:z.array(z.string().max(500)).max(500),journal:z.string().max(2000).nullable(),year:z.number().int().min(1000).max(2100).nullable(),abstract:z.string().max(80000).nullable(),doi:z.string().max(500).nullable(),citations:z.number().nonnegative().nullable(),openAccess:z.boolean().nullable(),type:z.string().max(100),provider:z.enum(['OpenAlex','Crossref','Demo']),url:webUrl,fullTextUrl:webUrl,demo:z.boolean(),score:z.number().optional(),matchedTerms:z.array(z.string()).optional()}).refine(p=>p.demo===(p.provider==='Demo'),'Demo origin must match provider');
const editFields={status:z.enum(['Unread','Reading','Completed']),collection:z.string().trim().min(1).max(80),notes:z.string().max(20000),favorite:z.boolean()};
export const actionSchema=z.discriminatedUnion('action',[
 z.object({action:z.literal('create_project'),title:z.string().trim().min(3).max(150),question:z.string().trim().min(5).max(2000),framework:z.enum(['PICO','PICOS','PECO','SPIDER','Custom'])}),
 z.object({action:z.literal('save_paper'),paper:paperSchema,projectId:z.string().min(1)}),
 z.object({action:z.literal('update_saved'),paperId:z.string().min(1),projectId:z.string().min(1),...editFields}),
 z.object({action:z.literal('remove_saved'),paperId:z.string().min(1),projectId:z.string().min(1)})
]);
