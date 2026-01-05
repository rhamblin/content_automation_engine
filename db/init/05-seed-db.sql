-- seed_data.sql
-- Only seed if identity.tenants is empty
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM identity.tenants) THEN

    -- 1. Identity: Tenant, User, Tenant-User mapping, Project
    INSERT INTO identity.tenants (tenant_id, name, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000001', 'DevTenant', NOW());

    INSERT INTO identity.users (user_id, email, provider, provider_sub, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000002', 'dev-admin@example.com', 'dev-bypass', 'dev-admin', NOW());

    INSERT INTO identity.tenant_users (tenant_id, user_id, role)
    VALUES
      ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'admin');

    INSERT INTO identity.projects (project_id, tenant_id, name, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'Phase1Project', NOW());

    -- 2. Domain Data: Niche & Keywords
    INSERT INTO niches.niches (niche_id, name, domain, default_budget, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000004', 'Sports Sneakers', 'https://www.chefexotic.com', 100, NOW());

    INSERT INTO niches.keywords (keyword_id, niche_id, name)
    VALUES
      ('00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000004', 'running shoes'),
      ('00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000004', 'basketball sneakers'),
      ('00000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000004', 'squishy soccer cleats with no laces');

    -- 3. Integration Profile for Pinterest
    INSERT INTO integration_profiles (
      integration_profile_id,
      project_id,
      niche_id,
      channel_key,
      settings,
      created_at
    ) VALUES (
      '00000000-0000-0000-0000-000000000007',
      '00000000-0000-0000-0000-000000000003',
      '00000000-0000-0000-0000-000000000004',
      'pinterest',
      '{"default_budget":50,"post_dimensions":"1000x1500"}',
      NOW()
    );

    -- 4. Sample Content
    INSERT INTO contents.contents (
      content_id,
      integration_profile_id,
      asset_url,
      title,
      description,
      hashtags,
      status,
      created_at
    ) VALUES (
      '00000000-0000-0000-0000-000000000008',
      '00000000-0000-0000-0000-000000000007',
      's3://dev-bucket/sneaker1.png',
      'Top-Rated Running Shoes',
      'Check out these top-rated running shoes for ultimate comfort and style.',
      ARRAY['running','sneakers','fitness'],
      'draft',
      NOW()
    );

    -- 5. Sample Content Publication (published to Pinterest)
    INSERT INTO contents.content_publications (
      publication_id,
      content_id,
      channel_key,
      platform_post_id,
      published_at,
      platform_metadata
    ) VALUES (
      '00000000-0000-0000-0000-000000000009',
      '00000000-0000-0000-0000-000000000008',
      'pinterest',
      '1234567890',
      NOW() - INTERVAL '1 day',
      '{"board_id": "abc123", "section_id": null}'
    );

    -- 6. Sample Analytics Metric (for yesterday)
    INSERT INTO analytics.metrics (content_id, date, impressions, clicks, saves)
    VALUES
      ('00000000-0000-0000-0000-000000000008', CURRENT_DATE - INTERVAL '1 day', 150, 12, 3);

  END IF;
END
$$;
