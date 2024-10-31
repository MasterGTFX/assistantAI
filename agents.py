from dotenv import load_dotenv
import os
from datetime import datetime

from openai import OpenAI
from swarm import Swarm, Agent
from gmail import read_emails, write_email, search_for_emails, get_email_by_id
from google_calendar import list_upcoming_events, create_event, delete_event, update_event
from x import send_tweet
from spotify import play, get_current_track, control_playback, search

# Load environment variables
load_dotenv()

# Load context variables from environment
default_context = {
    "user_name": os.getenv("USER_NAME", "User"),
    "email": os.getenv("USER_EMAIL", "unknown@example.com"),
    "preferred_language": os.getenv("PREFERRED_LANGUAGE", "English"),
    "location": os.getenv("USER_LOCATION", "N/A"),
    "twitter_username": os.getenv("TWITTER_USERNAME", "N/A"),
    "tweet_preferred_language": os.getenv("TWEET_PREFERRED_LANGUAGE", "English"),
    "current_datetime": datetime.now().isoformat(),
}


def base_assistant_instructions(context_variables):
    user_name = context_variables.get("user_name", "User")
    preferred_language = context_variables.get("preferred_language", "English")
    location = context_variables.get("location", "N/A")
    current_datetime = context_variables.get("current_datetime", datetime.now().isoformat())

    return f"""
    You are a personal assistant for {user_name}. You coordinate between specialized agents for email, calendar, and social media tasks.
    Use the following user information to personalize your responses:
    - User Name: {user_name}
    - Preferred Language: {preferred_language}
    - Location: {location}
    - Current Date/Time: {current_datetime}

    Always address the user by their name and consider their location and preferred language when responding.
    Direct specific tasks to the appropriate specialized agent.
    """


def email_assistant_instructions(context_variables):
    return f"""
    You are an email management specialist for {context_variables.get('user_name', 'User')}.
    User Email: {context_variables.get('email', 'N/A')}
    Preferred Language: {context_variables.get('preferred_language', 'English')}
    
    You can:
    - Read and search emails
    - Get detailed information about specific emails
    - Write and send emails
    
    You cannot:
    - Delete emails
    - Manage calendar events
    
    Rules:
    - Before sending an email, confirm with User the email content and recipients.
    - IMPORTANT: Do not send an email without User's approval.
    - Always use get_email_by_id function with the appropriate email ID for detailed email content queries.
    - When reading an email, provide a summary of the email content.
    """


def calendar_assistant_instructions(context_variables):
    return f"""
    You are a calendar management specialist for {context_variables.get('user_name', 'User')}.
    Current Datetime: {context_variables.get('current_datetime', datetime.now().isoformat())}
    User Preferred Language: {context_variables.get('preferred_language', 'English')}
    User Location: {context_variables.get('location', 'N/A')}
    
    You can:
    - List upcoming events
    - Create new calendar events
    - Update existing events
    - Delete events
    
    Rules:
    - Always confirm event details with User before creating, updating, or deleting events.
    
    Important: Always handle dates and times in ISO format and consider the user's timezone.
    """


def social_media_assistant_instructions(context_variables):
    return f"""
    You are a social media specialist for {context_variables.get('user_name', 'User')}.
    Twitter Username: {context_variables.get('twitter_username', 'N/A')}
    User Language: {context_variables.get('tweet_preferred_language', 'Polish')}
    
    You can:
    - Send tweets on User's Twitter account with engaging content.
    
    Rules:
    - Always confirm the tweet content with User before posting.
    - IMPORTANT: Do not post before User's approval.
    - Tweet content should be engaging.
    - Use the tweet_preferred_language to determine the language of the tweet.
    """


def music_assistant_instructions(context_variables):
    return f"""
    You are a music assistant for {context_variables.get('user_name', 'User')}.
    Preferred Language: {context_variables.get('preferred_language', 'English')}
    
    You can:
    - Search for content on Spotify (tracks, albums, artists, playlists)
    - Play content by URI
    - Control playback (play, pause, next, previous)
    - Get information about currently playing track

    Rules:
    - When just searching, provide to User the most important information about the content
    - Provide content information when starting playback
    - Always handle errors gracefully and inform the user if there are any playback issues
    - Note that only tracks, albums, artists, and playlists can be played directly
    - For shows, episodes, and audiobooks, you can only search and provide information
    """


# Specialized Agents
base_agent = Agent(
    name="Base Assistant",
    instructions=base_assistant_instructions,
    model=os.getenv("default_model", "gpt-4o-mini")
)

email_agent = Agent(
    name="Email Assistant",
    instructions=email_assistant_instructions,
    model=os.getenv("default_model", "gpt-4o-mini"),
    functions=[
        read_emails,
        get_email_by_id,
        search_for_emails,
        write_email,
    ]
)

calendar_agent = Agent(
    name="Calendar Assistant",
    instructions=calendar_assistant_instructions,
    model=os.getenv("default_model", "gpt-4o-mini"),
    functions=[
        list_upcoming_events,
        create_event,
        delete_event,
        update_event,
    ]
)

social_media_agent = Agent(
    name="Social Media Assistant",
    instructions=social_media_assistant_instructions,
    model=os.getenv("default_model", "gpt-4o-mini"),
    functions=[
        send_tweet
    ]
)

music_agent = Agent(
    name="Music Assistant",
    instructions=music_assistant_instructions,
    model=os.getenv("default_model", "gpt-4o-mini"),
    functions=[
        play,
        search,
        get_current_track,
        control_playback,
    ]
)


# Transfer Functions
def transfer_to_email_agent():
    """ Transfer to the Email Assistant """
    return email_agent


def transfer_to_calendar_agent():
    """ Transfer to the Calendar Assistant """
    return calendar_agent


def transfer_to_social_media_agent():
    """ Transfer to the Social Media (Twitter/X) Assistant """
    return social_media_agent


def transfer_to_music_agent():
    """ Transfer to the Music (Spotify) Assistant """
    return music_agent


def transfer_back_to_base_agent():
    """ Transfer back to the Assistant. Call this function after completing your task.
IMPORTANT: if a user is asking about a topic that is not handled by the current agent also transfer back to the base agent."""
    return base_agent


base_agent.functions = [
    transfer_to_email_agent, 
    transfer_to_calendar_agent, 
    transfer_to_social_media_agent,
    transfer_to_music_agent
]
email_agent.functions.append(transfer_back_to_base_agent)
calendar_agent.functions.append(transfer_back_to_base_agent)
social_media_agent.functions.append(transfer_back_to_base_agent)
music_agent.functions.append(transfer_back_to_base_agent)

# Example usage
if __name__ == "__main__":
    # Initialize the Swarm client
    # gets API Key from environment variable OPENAI_API_KEY
    openai_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("llm_api_key"),
    )
    client = Swarm(client=openai_client)

    response = client.run(
        agent=base_agent,
        messages=[{"role": "user", "content": "Can you check my today unread emails?"}],
        context_variables=default_context
    )

    print("\nFinal response:")
    print(response.messages[-1]["content"])
    print(f"Current agent: {response.agent.name}")
    print(f"Context variables: {response.context_variables}")
