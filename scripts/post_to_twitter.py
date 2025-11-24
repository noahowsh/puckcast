#!/usr/bin/env python3
"""
Post to X/Twitter using the official API.

Uses the A/B testing framework to generate optimized content and posts it to Twitter.
Requires Twitter API v2 credentials (OAuth 2.0).
"""

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import tweepy

# Import the A/B testing module
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from twitter_ab_testing import (
    load_predictions,
    load_variants,
    select_variant,
    generate_post,
    log_variant_usage,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Post predictions to X/Twitter"
    )
    parser.add_argument(
        "--post-type",
        choices=[
            "morning_preview", "afternoon_update", "evening_recap",
            "yesterday_results", "weekly_standings", "weekly_recap",
            "micro_insights", "game_of_night", "upset_watch",
            "team_surging", "team_dropping", "bold_predictions",
            "team_spotlight", "yesterdays_surprises", "weekly_power_index",
            "overrated_poll", "model_accountability", "fun_fact"
        ],
        required=True,
        help="Type of post to create",
    )
    parser.add_argument(
        "--variant",
        help="Force specific variant (A, B, C, etc.). Random if not specified for A/B testing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate post but don't actually tweet it",
    )
    parser.add_argument(
        "--site-url",
        default="https://puckcast.ai",
        help="Website URL to include in posts",
    )
    return parser.parse_args()


def get_twitter_client():
    """Initialize Twitter API client with credentials from environment."""

    try:
        import tweepy  # type: ignore
    except ImportError:
        print("❌ tweepy not installed. Install with: pip install tweepy")
        sys.exit(1)

    # Get credentials from environment variables
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    # Check if credentials are available
    missing = []
    if not api_key:
        missing.append("TWITTER_API_KEY")
    if not api_secret:
        missing.append("TWITTER_API_SECRET")
    if not access_token:
        missing.append("TWITTER_ACCESS_TOKEN")
    if not access_secret:
        missing.append("TWITTER_ACCESS_SECRET")

    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("\nSet these in your environment or GitHub Secrets:")
        print("  export TWITTER_API_KEY='your_api_key'")
        print("  export TWITTER_API_SECRET='your_api_secret'")
        print("  export TWITTER_ACCESS_TOKEN='your_access_token'")
        print("  export TWITTER_ACCESS_SECRET='your_access_secret'")
        sys.exit(1)

    # Initialize client with OAuth 1.0a User Context
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
        bearer_token=bearer_token,  # Optional but recommended
    )

    return client


def _upload_media(api_key: str, api_secret: str, access_token: str, access_secret: str, image_path: Path):
    """Upload media via v1.1 API (tweepy.API) and return media_id."""
    import tweepy  # type: ignore

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api = tweepy.API(auth)
    media = api.media_upload(str(image_path))
    return media.media_id


def post_tweet(
    client: Optional["tweepy.Client"],
    content: str,
    *,
    dry_run: bool = False,
    image_path: Path | None = None,
) -> Optional[dict]:
    """Post a tweet and return the response."""

    if dry_run:
        print("\n" + "="*70)
        print("🔍 DRY RUN - Would post this tweet:")
        print("="*70)
        print(content)
        print("="*70)
        print(f"\n📏 Character count: {len(content)}/280")
        return None

    try:
        import tweepy  # type: ignore

        media_ids = None
        if image_path and image_path.exists():
            print(f"🖼  Attaching image: {image_path}")
            try:
                api_key = os.getenv("TWITTER_API_KEY", "")
                api_secret = os.getenv("TWITTER_API_SECRET", "")
                access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
                access_secret = os.getenv("TWITTER_ACCESS_SECRET", "")
                media_id = _upload_media(api_key, api_secret, access_token, access_secret, image_path)
                media_ids = [media_id]
            except Exception as media_err:  # noqa: BLE001 - want to keep posting even if media fails
                print(f"⚠️  Media upload failed, posting without image: {media_err}")

        # Post the tweet
        response = client.create_tweet(text=content, media_ids=media_ids)  # type: ignore[union-attr]

        # Extract tweet ID
        tweet_id = response.data['id']
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

        print(f"\n✅ Tweet posted successfully!")
        print(f"🔗 URL: {tweet_url}")
        print(f"📊 Tweet ID: {tweet_id}")

        return {
            "id": tweet_id,
            "url": tweet_url,
            "text": content,
        }

    except tweepy.TweepyException as e:
        print(f"\n❌ Error posting tweet: {e}")
        sys.exit(1)


def main() -> None:
    args = parse_args()

    print("🏒 Puckcast Twitter Automation")
    print("="*70)

    # Load predictions and variants
    try:
        data = load_predictions()
        variants = load_variants()
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        sys.exit(1)

    # Select variant (random for A/B testing or forced)
    variant = select_variant(args.post_type, variants, args.variant)
    print(f"📋 Selected variant: {variant['id']} ({variant['format']})")

    # Generate post content
    post_content = generate_post(args.post_type, variant, data)

    # Replace placeholder URL with actual site URL
    post_content = post_content.replace("[your-site-url]", args.site_url)

    # Check character limit
    if len(post_content) > 280:
        print(f"⚠️  Warning: Post is {len(post_content)} characters (limit: 280)")
        print("Post will be truncated by Twitter!")

    # Initialize Twitter client (unless dry run)
    client = None
    if not args.dry_run:
        client = get_twitter_client()

    # Social sharing image (optional)
    social_image = REPO_ROOT / "web" / "public" / "puckcastsocial.png"
    if args.dry_run:
        social_image = None  # skip media in dry-run for speed

    # Post the tweet
    result = post_tweet(client, post_content, dry_run=args.dry_run, image_path=social_image if social_image and social_image.exists() else None)

    # Log variant usage for A/B testing analysis
    if not args.dry_run:
        log_variant_usage(args.post_type, variant)
        print(f"📝 Logged A/B test variant for analysis")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
