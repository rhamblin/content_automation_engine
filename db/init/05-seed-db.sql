-- seed_data.sql
-- Only seed if tenants is empty
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM tenants) THEN

    -- 1. Core entities: Tenant, User, Channel
    INSERT INTO tenants (id, external_id, title, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000101', 'DevTenant', NOW());

    INSERT INTO users (id, external_id, is_active, email, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000102', true, 'dev-admin@example.com', NOW());

    INSERT INTO channels (id, external_id, identifier, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000110', 'pinterest', NOW());
    -- 2. Junction tables
    INSERT INTO tenants_users (tenant_id, user_id, role, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'admin', NOW());

    INSERT INTO users_identity_providers (user_id, identity_provider_user_id, identity_provider, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000202', 'azure_b2c', NOW());

    INSERT INTO tenants_channels (tenant_id, channel_id, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010', NOW());
    -- 3. Project
    INSERT INTO projects (id, external_id, tenant_id, name, is_active, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000103', '00000000-0000-0000-0000-000000000001', 'Phase1Project', true, NOW());

    -- 4. Niche & Keywords
    INSERT INTO niches (id, external_id, tenant_id, title, is_active, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000001', 'Sports Sneakers', true, NOW());

    INSERT INTO keywords (id, external_id, tenant_id, niche_id, term, is_active, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000105', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', 'running shoes', true, NOW()),
      ('00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000106', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', 'basketball sneakers', true, NOW()),
      ('00000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000107', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', 'soccer cleats', true, NOW());

    -- 5. Integration Profile
    INSERT INTO integration_profiles (id, external_id, tenant_id, niche_id, project_id, channel_id, is_active, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000108', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000010', true, NOW());

    -- 6. Sample Image
    INSERT INTO images (id, external_id, tenant_id, niche_id, keyword_id, kind, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000020', '00000000-0000-0000-0000-000000000120', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000005', 'original', NOW());

    -- 7. Sample Content
    INSERT INTO contents (id, external_id, tenant_id, niche_id, keyword_id, title, description, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000030', '00000000-0000-0000-0000-000000000130', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000005', 'Top-Rated Running Shoes', 'Check out these top-rated running shoes for ultimate comfort and style.', NOW());

    -- 8. Sample Render
    INSERT INTO renders (id, external_id, tenant_id, content_id, niche_id, keyword_id, input_image_id, style_name, status, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000040', '00000000-0000-0000-0000-000000000140', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000030', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000020', 'modern', 'completed', NOW());

    -- 9. Sample Publication
    INSERT INTO publications (id, external_id, tenant_id, render_id, channel_id, content_id, post_id, status, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000050', '00000000-0000-0000-0000-000000000150', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000040', '00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000030', '1234567890', 'published', NOW());

    -- 10. Sample Publication Metric
    INSERT INTO publication_metrics (id, external_id, tenant_id, publication_id, channel_id, snapshot_date, metrics, fetched_at)
    VALUES
      ('00000000-0000-0000-0000-000000000060', '00000000-0000-0000-0000-000000000160', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000050', '00000000-0000-0000-0000-000000000010', NOW() - INTERVAL '1 day', '{"impressions": 150, "clicks": 12, "saves": 3}', NOW());

    -- 11. Schedules (one per message type)
    INSERT INTO schedules (id, external_id, tenant_id, integration_profile_id, is_active, cron_expression, message_type, created_at)
    VALUES
      -- Content generation (tied to integration profile)
      ('00000000-0000-0000-0000-000000000070', '00000000-0000-0000-0000-000000000170', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000008', true, '* * * * *', 'content_generation_requested', NOW()),
      -- Tenant-level schedules (no integration profile)
      ('00000000-0000-0000-0000-000000000071', '00000000-0000-0000-0000-000000000171', '00000000-0000-0000-0000-000000000001', NULL, true, '* * * * *', 'promotion_orchestrator_requested', NOW()),
      ('00000000-0000-0000-0000-000000000072', '00000000-0000-0000-0000-000000000172', '00000000-0000-0000-0000-000000000001', NULL, true, '* * * * *', 'collect_analytics_requested', NOW()),
      ('00000000-0000-0000-0000-000000000073', '00000000-0000-0000-0000-000000000173', '00000000-0000-0000-0000-000000000001', NULL, true, '* * * * *', 'activity_report_requested', NOW());

  END IF;
END
$$;
