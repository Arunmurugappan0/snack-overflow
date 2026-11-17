ALTER TABLE vote
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_vote_user_snack'
          AND conrelid = 'vote'::regclass
    ) THEN
        ALTER TABLE vote
            ADD CONSTRAINT uq_vote_user_snack UNIQUE (user_id, snack_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_user_role'
    ) THEN
        ALTER TABLE "user"
            ADD CONSTRAINT ck_user_role CHECK (role IN ('admin', 'member'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_activity_action'
    ) THEN
        ALTER TABLE activity
            ADD CONSTRAINT ck_activity_action CHECK (action IN ('consumed', 'restocked'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_activity_amount_positive'
    ) THEN
        ALTER TABLE activity
            ADD CONSTRAINT ck_activity_amount_positive CHECK (amount > 0);
    END IF;
END;
$$;
