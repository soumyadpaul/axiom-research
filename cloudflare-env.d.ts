declare namespace Cloudflare {
  interface Env {
    DB?: D1Database;
    ASSETS?: Fetcher;
    ACCESS_TEAM_DOMAIN?: string;
    ACCESS_AUD?: string;
    OPENALEX_API_KEY?: string;
    CROSSREF_MAILTO?: string;
  }
}
