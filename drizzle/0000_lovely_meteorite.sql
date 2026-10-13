CREATE TABLE `projects` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`title` text NOT NULL,
	`question` text NOT NULL,
	`framework` text NOT NULL,
	`demo` text DEFAULT 'false' NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_projects_owner` ON `projects` (`owner_id`);--> statement-breakpoint
CREATE TABLE `saved_papers` (
	`owner_id` text NOT NULL,
	`paper_id` text NOT NULL,
	`project_id` text NOT NULL,
	`metadata` text NOT NULL,
	`status` text DEFAULT 'Unread' NOT NULL,
	`collection` text DEFAULT 'Background' NOT NULL,
	`notes` text DEFAULT '' NOT NULL,
	`favorite` text DEFAULT 'false' NOT NULL,
	PRIMARY KEY(`owner_id`, `paper_id`, `project_id`),
	FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_saved_project` ON `saved_papers` (`project_id`);