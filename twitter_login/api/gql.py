from __future__ import annotations

import json
from logging import getLogger
from typing import TYPE_CHECKING, Any

from curl_cffi import Response

from ..gql_endpoints.endpoint import Endpoint, GQLState
from ..headers import HeadersConfig
from .utils import UNSET, remove_unset

if TYPE_CHECKING:
    from ..http import HTTPClient

logger = getLogger(__name__)


class GQLClient:
    def __init__(self, http: HTTPClient, state: GQLState) -> None:
        self.http = http
        self.endpoints = state.endpoints
        self.feature_switches = state.feature_switches

    async def get(self, endpoint: Endpoint, variables: dict[str, Any] | None = None, field_toggles: dict[str, bool] | None = None, referer = None) -> Response:
        headers_config = HeadersConfig.general_api(referer=referer, extra_headers={
            'x-twitter-active-user': 'yes',
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-client-language': 'en'
        })
        params = {}
        features = endpoint.features
        if variables is not None:
            params['variables'] = json.dumps(remove_unset(variables))
        if features is not None:
            params['features'] = json.dumps(features)
        if field_toggles is not None:
            params['field_toggles'] = json.dumps(field_toggles)
        response = await self.http.get(
            endpoint.url,
            headers_config,
            params=params
        )
        logger.info(f'GraphQL GET {endpoint.url}')
        return response

    async def post(self, endpoint: Endpoint, variables: dict[str, Any] | None = None, add_query_id: bool = False, referer = None) -> Response:
        headers_config = HeadersConfig.general_api(referer=referer, extra_headers={
            'x-twitter-active-user': 'yes',
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-client-language': 'en'
        })
        data = {}
        features = endpoint.features
        if variables is not None:
            data['variables'] = remove_unset(variables)
        if features is not None:
            data['features'] = features
        if add_query_id:
            data['queryId'] = endpoint.queryId
        response = await self.http.post(
            endpoint.url,
            headers_config,
            json=data
        )
        logger.info(f'GraphQL POST {endpoint.url}')
        return response

    async def TweetDetail(self, *, focalTweetId, cursor, referrer, controller_data, rankingMode):
        """
        All params: focalTweetId, cursor, referrer, controller_data, rux_context, with_rux_injections, rankingMode,
                    includePromotedContent, withCommunity, withQuickPromoteEligibilityTweetFields, withBirdwatchNotes, withVoice, isReaderMode

        Params:
            focalTweetId:
                Tweet ID
            cursor:
                base64 encoded thrift data (Not required)
            referrer:
                The page where the tweet was referred to
                [Known options]
                "home" - from timeline page
                "me" - Own profile page
                "profile" - from user profile page
                "tweet" - from tweet replies page
                "grok" - from grok chat
                "full_tweet_activity" - quote
                "bookmarks" - bookmarks page
                "search" - search page
            controller_data:
                base64 encoded thrift data (Not required)
            with_rux_injections:
                Unknown (mostly False)
            rankingMode:
                [options]
                "Relevance"
                "Recency"
                "Likes"
            includePromotedContent:
                True (fixed)
            withCommunity:
                Corresponds to "c9s_enabled" feature switch
            withQuickPromoteEligibilityTweetFields:
                True (fixed)
            withBirdwatchNotes:
                Corresponds to "responsive_web_birdwatch_consumption_enabled" feature switch
            withVoice:
                Corresponds to "voice_consumption_enabled" feature switch

        Unknown Params:
            rux_context, isReaderMode
        """
        variables = {
            'focalTweetId': focalTweetId,
            'cursor': cursor or UNSET,
            'referrer': referrer,
            'controller_data': controller_data or UNSET,
            'with_rux_injections': False,
            'rankingMode': rankingMode,
            'includePromotedContent': True,
            'withCommunity': self.feature_switches.get('c9s_enabled'),
            'withQuickPromoteEligibilityTweetFields': True,
            'withBirdwatchNotes': self.feature_switches.get('responsive_web_birdwatch_consumption_enabled'),
            'withVoice': self.feature_switches.get('voice_consumption_enabled')
        }
        field_toggles = {
            'withArticleRichContentState': self.feature_switches.get('responsive_web_twitter_article_seed_tweet_detail_enabled'),
            'withArticlePlainText': False,
            'withGrokAnalyze': self.feature_switches.get('subscriptions_inapp_grok_analyze'),
            'withDisallowedReplyControls': self.feature_switches.get('disallowed_reply_controls_callout_enabled')
        }
        return await self.get(
            self.endpoints['TweetDetail'],
            variables,
            field_toggles,
            referer=f'https://x.com/i/status/{focalTweetId}'
        )

    async def CreateTweet(self, *, tweet_text, card_uri, attachment_url, reply, batch_compose, geo, media, conversation_control):
        """
        All params: tweet_text, card_uri, attachment_url, reply, batch_compose, geo, dark_request, media,
                    semantic_annotation_ids, conversation_control, content_disclosure, exclusive_tweet_control_options,
                    edit_options, premium_tweet_control_options, richtext_options, media_options, broadcast, disallowed_reply_options
        Options:
            tweet_text:
                Tweet text
            card_uri:
                Poll uri (Not required)
            attachment_url:
                Quoted tweet url (Not required)
            reply:
                Reply data (Not required)
                {'in_reply_to_tweet_id': '111111', 'exclude_reply_user_ids': ['222222', '333333']}
            batch_compose:
                For tree tweet (Not required)
                "BatchFirst" - Tree first tweet
                "BatchSubsequent" - Tree sub-tweet
            geo:
                geo data (Not required)
                {'place_id': ...}
            dark_request:
                mostly False
            media:
                {'media_entities': [...], 'possibly_sensitive': False}
            semantic_annotation_ids:
                mostly empty list []
            conversation_control:
                (Not required)
                {'mode': 'Community'}
                {'mode': 'ByInvitation'}
                {'mode': 'Subscribers'}
                {'mode': 'Verified'}
                {'mode': 'Premium'}
            edit_options, premium_tweet_control_options, richtext_options:
                Premium features not implemented yet (Not required)
            disallowed_reply_options:
                mostly None

        Unknown Params:
            content_disclosure, exclusive_tweet_control_options, media_options, broadcast
        """
        variables = {
            'tweet_text': tweet_text,
            'card_uri': card_uri or UNSET,
            'attachment_url': attachment_url or UNSET,
            'reply': reply or UNSET,
            'batch_compose': batch_compose or UNSET,
            'geo': geo or UNSET,
            'dark_request': False,
            'media': media,
            'semantic_annotation_ids': [],
            'conversation_control': conversation_control,
            'disallowed_reply_options': None
        }
        return await self.post(
            self.endpoints['CreateTweet'],
            variables,
            add_query_id=True,
            referer='https://x.com/compose/post'
        )

    def test(self):
        """self.endpoints['SearchTimeline']
        self.endpoints['SimilarPosts']
        self.endpoints['CreateNoteTweet']
        self.endpoints['CreateTweet']
        self.endpoints['CreateScheduledTweet']
        self.endpoints['DeleteTweet']
        self.endpoints['UserByScreenName']
        self.endpoints['UserByRestId']
        self.endpoints['TweetDetail']
        self.endpoints['TweetResultByRestId']
        self.endpoints['FetchScheduledTweets']
        self.endpoints['DeleteScheduledTweet']
        self.endpoints['Retweeters']
        self.endpoints['Favoriters']
        self.endpoints['BirdwatchFetchOneNote']
        self.endpoints['UserTweets']
        self.endpoints['UserTweetsAndReplies']
        self.endpoints['UserMedia']
        self.endpoints['Likes']
        self.endpoints['UserHighlightsTweets']
        self.endpoints['HomeTimeline']
        self.endpoints['HomeLatestTimeline']
        self.endpoints['FavoriteTweet']
        self.endpoints['UnfavoriteTweet']
        self.endpoints['CreateRetweet']
        self.endpoints['DeleteRetweet']
        self.endpoints['CreateBookmark']
        self.endpoints['bookmarkTweetToFolder']
        self.endpoints['DeleteBookmark']
        self.endpoints['Bookmarks']
        self.endpoints['BookmarkFolderTimeline']
        self.endpoints['BookmarksAllDelete']
        self.endpoints['BookmarkFoldersSlice']
        self.endpoints['EditBookmarkFolder']
        self.endpoints['DeleteBookmarkFolder']
        self.endpoints['createBookmarkFolder']
        self.endpoints['Followers']
        self.endpoints['BlueVerifiedFollowers']
        self.endpoints['FollowersYouKnow']
        self.endpoints['Following']
        self.endpoints['UserCreatorSubscriptions']
        self.endpoints['useDMReactionMutationAddMutation']
        self.endpoints['useDMReactionMutationRemoveMutation']
        self.endpoints['DMMessageDeleteMutation']
        self.endpoints['AddParticipantsMutation']
        self.endpoints['CreateList']
        self.endpoints['EditListBanner']
        self.endpoints['DeleteListBanner']
        self.endpoints['UpdateList']
        self.endpoints['ListAddMember']
        self.endpoints['ListRemoveMember']
        self.endpoints['ListsManagementPageTimeline']
        self.endpoints['ListByRestId']
        self.endpoints['ListLatestTweetsTimeline']
        self.endpoints['ListMembers']
        self.endpoints['ListSubscribers']
        self.endpoints['CommunitiesSearchQuery']
        self.endpoints['CommunityQuery']
        self.endpoints['CommunityMediaTimeline']
        self.endpoints['CommunityTweetsTimeline']
        self.endpoints['CommunitiesMainPageTimeline']
        self.endpoints['JoinCommunity']
        self.endpoints['LeaveCommunity']
        self.endpoints['RequestToJoinCommunity']
        self.endpoints['membersSliceTimeline_Query']
        self.endpoints['moderatorsSliceTimeline_Query']
        self.endpoints['CommunityTweetSearchModuleQuery']
        self.endpoints['TweetResultsByRestIds']"""