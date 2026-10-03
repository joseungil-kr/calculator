import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const sourceRef = z.object({
  name: z.string(),
  url: z.string().url(),
  type: z.enum(['official', 'facility', 'education', 'professional', 'business', 'reference']).default('reference'),
  verifiedAt: z.coerce.date().optional(),
});

const articles = defineCollection({
  loader: glob({ pattern: 'yongin-*.md', base: './src/content/articles' }),
  schema: z.object({
    pageKey: z.string(),
    snapshotId: z.string(),
    sourceDraftKey: z.string(),
    sourceRecordId: z.string(),
    slug: z.string(),
    routeType: z.enum(['category']),
    title: z.string(),
    description: z.string(),
    h1: z.string().optional(),
    cardSummary: z.string().optional(),
    firstAnswer: z.string().optional(),
    queryClass: z.string().optional(),
    visualIntent: z.string().optional(),
    assetSlot: z.string().optional(),
    category: z.enum(['funeral', 'business', 'school', 'event', 'gift', 'order', 'regions']),
    structureType: z.string(),
    pageType: z.enum([
      'regional-service',
      'funeral-facility',
      'business-opening',
      'school-event',
      'event-venue',
      'hospital-visit',
      'personal-gift',
      'station-transit',
      'order-help',
      'price-guide',
      'message-guide'
    ]),
    contentRole: z.enum(['question-answer']).default('question-answer'),
    localizationPolicy: z.enum(['local-required', 'local-optional']).default('local-required'),
    region: z.string(),
    verifiedAt: z.coerce.date().optional(),
    publishedAt: z.coerce.date().optional(),
    updatedAt: z.coerce.date().optional(),
    regionalPurchaseMode: z.enum(['catalog','consultation-only']).optional(),
    regionalProductKeys: z.array(z.string()).optional(),
    regionalProductFamilies: z.array(z.string()).optional(),
    ogImageWidth: z.number().optional(),
    ogImageHeight: z.number().optional(),
    ogImageType: z.string().optional(),
    scopeKey: z.string().optional(),
    regionUnitKeys: z.array(z.string()).optional(),
    ogImageSha256: z.string().optional(),
    ogImageSourceUrl: z.string().url().optional(),
    ogImage: z.string().optional(),
    ogImageAlt: z.string().optional(),
    sourceUrls: z.array(z.string().url()).default([]),
    sources: z.array(sourceRef).default([]),
    relatedPageKeys: z.array(z.string()).default([]),
    draftStatus: z.enum(['approved', 'published']).default('approved'),
  }),
});

export const collections = { articles };
