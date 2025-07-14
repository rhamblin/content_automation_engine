DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM niches.niches) THEN

    INSERT INTO niches.niches (name, domain, default_budget)
    VALUES 
      ('Travel', 'travelbuzz.com', 1000),
      ('Fitness', 'fitlife.io', 1500);

    INSERT INTO niches.keywords (niche_id, keyword)
    SELECT niche_id, kw FROM (
      VALUES 
        ('Travel', 'backpacking'),
        ('Travel', 'solo travel'),
        ('Fitness', 'yoga'),
        ('Fitness', 'workout')
    ) AS seed(name, kw)
    JOIN niches.niches n ON n.name = seed.name;

  END IF;
END $$;