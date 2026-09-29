import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    pageKey: z.string(),
    snapshotId: z.string(),
    sourceDraftKey: z.string(),
    sourceRecordId: z.string(),
    slug: z.string(),
    routeType: z.enum(['top_level', 'category']),
    title: z.string(),
    description: z.string(),
    category: z.enum(['guide', 'places', 'occasions', 'flower-knowledge', 'order-help']),
    structureType: z.string(),
    region: z.string(),
    verifiedAt: z.coerce.date().optional(),
    publishedAt: z.coerce.date().optional(),
    updatedAt: z.coerce.date().optional(),
    ogImage: z.string().optional(),
    ogImageAlt: z.string().optional(),
    sourceUrls: z.array(z.string().url()).default([]),
    draftStatus: z.enum(['approved', 'published']).default('approved'),
  }),
});

export const collections = { articles };
