import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const sourceRef = z.object({
  name: z.string(),
  url: z.string().url(),
  type: z.enum(['official', 'facility', 'education', 'professional', 'reference']).default('reference'),
  verifiedAt: z.coerce.date().optional(),
});

const articles = defineCollection({
  loader: glob({ pattern: 'suwon-flower-v12-*.md', base: './src/content/articles' }),
  schema: z.object({
    pageKey: z.string(),
    snapshotId: z.string(),
    sourceDraftKey: z.string(),
    sourceRecordId: z.string(),
    slug: z.string(),
    routeType: z.enum(['category']),
    title: z.string(),
    description: z.string(),
    cardSummary: z.string(),
    category: z.enum(['funeral', 'business', 'school', 'event', 'gift', 'order']),
    structureType: z.string(),
    pageType: z.enum(['funeral-facility','business-opening','school-event','event-venue','hospital-visit','personal-gift','station-transit','order-help','price-guide','message-guide']),
    contentRole: z.enum(['commercial-landing', 'informational-pillar', 'question-answer']).default('question-answer'),
    localizationPolicy: z.enum(['local-required', 'local-optional', 'global']).default('local-optional'),
    region: z.string(),
    verifiedAt: z.coerce.date().optional(),
    publishedAt: z.coerce.date().optional(),
    updatedAt: z.coerce.date().optional(),
    ogImage: z.string().optional(),
    ogImageAlt: z.string().optional(),
    visualIntent: z.string().optional(),
    assetSlot: z.string().optional(),
    sourceUrls: z.array(z.string().url()).default([]),
    sources: z.array(sourceRef).default([]),
    relatedPageKeys: z.array(z.string()).default([]),
    draftStatus: z.enum(['approved', 'published']).default('approved'),
  }),
});

export const collections = { articles };
