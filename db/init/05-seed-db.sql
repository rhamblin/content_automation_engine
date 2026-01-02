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

    INSERT INTO niches.keywords (keyword_id, niche_id, keyword, keyword_image_match_confidence)
    VALUES
      ('00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000004', 'running shoes', 'high'),
      ('00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000004', 'squishy purple shoes with no laces', 'low'),
      ('00000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000004', 'athletic sneakers', 'high');


    -- 3. Integration Profile for Pinterest
    INSERT INTO integration_profiles (
      integration_profile_id,
      project_id,
      niche_id,
      text_provider_key,
      channel_key,
      settings,
      created_at
    ) VALUES (
      '00000000-0000-0000-0000-000000000007',
      '00000000-0000-0000-0000-000000000003',
      '00000000-0000-0000-0000-000000000004',
      'openai',
      'pinterest',
      '{"default_budget":50,"post_dimensions":"1000x1500"}',
      NOW()
    );


    -- 4. One Sample Post
    INSERT INTO posts.posts (
      post_id,
      integration_profile_id,
      asset_url,
      title,
      description,
      hashtags,
      status,
      last_posted_at,
      created_at
    ) VALUES (
      '00000000-0000-0000-0000-000000000008',
      '00000000-0000-0000-0000-000000000007',
      's3://dev-bucket/sneaker1.png',
      'Top-Rated Running Shoes',
      'Check out these top-rated running shoes for ultimate comfort and style.',
      ARRAY['running','sneakers','fitness'],
      'generated',
      NULL,
      NOW()
    );


    -- 5. Sample Analytics Metric (for yesterday)
    INSERT INTO analytics.metrics (post_id, date, impressions, clicks, saves)
    VALUES
      ('00000000-0000-0000-0000-000000000008', CURRENT_DATE - INTERVAL '1 day', 150, 12, 3);

  END IF;
END
$$;
