-- seed_data.sql
-- Only seed if tenants is empty
-- All FK references use external_id of the referenced entity
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
      ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000102', 'admin', NOW());

    INSERT INTO users_identity_providers (user_id, identity_provider_user_id, identity_provider, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000202', 'azure_b2c', NOW());

    INSERT INTO tenants_channels (tenant_id, channel_id, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000110', NOW());

    -- 3. Niche & Keywords
    INSERT INTO niches (id, external_id, tenant_id, title, is_active, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000101', 'Sports Sneakers', true, NOW());

    INSERT INTO keywords (id, external_id, tenant_id, niche_id, term, is_active, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000105', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000104', 'running shoes', true, NOW()),
      ('00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000106', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000104', 'basketball sneakers', true, NOW()),
      ('00000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000107', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000104', 'soccer cleats', true, NOW());

    -- 4. Integration Profile
    INSERT INTO integration_profiles (id, external_id, tenant_id, niche_id, channel_id, is_active, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000108', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000110', true, NOW());

    -- 5. Sample Image
    INSERT INTO images (id, external_id, tenant_id, niche_id, keyword_id, kind, uri, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000020', '00000000-0000-0000-0000-000000000120', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000105', 'original', 'blob://dev-tenant/images/sample-image.jpg', NOW());

    -- 6. Sample Content
    INSERT INTO contents (id, external_id, tenant_id, niche_id, keyword_id, title, description, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000030', '00000000-0000-0000-0000-000000000130', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000105', 'Top-Rated Running Shoes', 'Check out these top-rated running shoes for ultimate comfort and style.', NOW());

    -- 7. Sample Render
    INSERT INTO renders (id, external_id, tenant_id, content_id, niche_id, keyword_id, input_image_id, style_name, status, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000040', '00000000-0000-0000-0000-000000000140', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000130', '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000105', '00000000-0000-0000-0000-000000000120', 'modern', 'completed', NOW());

    -- 8. Sample Publication
    INSERT INTO publications (id, external_id, tenant_id, render_id, channel_id, content_id, post_id, status, created_at)
    VALUES
      ('00000000-0000-0000-0000-000000000050', '00000000-0000-0000-0000-000000000150', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000140', '00000000-0000-0000-0000-000000000110', '00000000-0000-0000-0000-000000000130', '1234567890', 'published', NOW());

    -- 9. Sample Publication Metric
    INSERT INTO publication_metrics (id, external_id, tenant_id, publication_id, channel_id, snapshot_date, metrics, fetched_at)
    VALUES
      ('00000000-0000-0000-0000-000000000060', '00000000-0000-0000-0000-000000000160', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000150', '00000000-0000-0000-0000-000000000110', NOW() - INTERVAL '1 day', '{"impressions": 150, "clicks": 12, "saves": 3}', NOW());

    -- 10. Schedules (one per message type)
    INSERT INTO schedules (id, external_id, tenant_id, integration_profile_id, is_active, cron_expression, message_type, created_at)
    VALUES
      -- Content generation (tied to integration profile)
      ('00000000-0000-0000-0000-000000000070', '00000000-0000-0000-0000-000000000170', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000108', true, '* * * * *', 'content_generation_requested', NOW()),
      -- Tenant-level schedules (no integration profile)
      ('00000000-0000-0000-0000-000000000071', '00000000-0000-0000-0000-000000000171', '00000000-0000-0000-0000-000000000101', NULL, true, '* * * * *', 'promotion_orchestrator_requested', NOW()),
      ('00000000-0000-0000-0000-000000000072', '00000000-0000-0000-0000-000000000172', '00000000-0000-0000-0000-000000000101', NULL, true, '* * * * *', 'collect_analytics_requested', NOW()),
      ('00000000-0000-0000-0000-000000000073', '00000000-0000-0000-0000-000000000173', '00000000-0000-0000-0000-000000000101', NULL, true, '* * * * *', 'activity_report_requested', NOW());

  END IF;
END
$$;
