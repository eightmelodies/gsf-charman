# Charman

## Overview

Charman (short for Character Manager) is a suite of tools that run and manage [Gemstone](https://gswiki.play.net) character sessions in [Lich](github.com/elanthia-online/lich-5). There are 3 components required for this all to work: 1) a daemon script that follows pre-configured rules to orchestrate chracter logon/logoff, 2) a Lich script that communicates character state and handles logoff requests, and 3) an API server that facilitates the communcation between the daemon and the Lich script.

## Components

### Daemon

Launches the Lich proxies based on configuration and talks to the API server to request logouts when needed.

#### Login strategies

Login strategies are the configuration that defines the priority when logging in characters. Strategies are created by implementing the LoginStrategy base class and given a list of characters they should return an ordered list of characters that should be logged in to accomplish the defined strategy.

Multiple strategies can be layered together to define more complex strategies. For example:
```
LOGIN_STRATEGIES = [WeeklyLumnisStrategy, WeeklyResourceStrategy]
...
```

When evaluating the first strategy (WeeklyLumnisStrategy) the daemon will short-circuit on that strategy if any viable characters are returned. This results in the daemon cycling through each character in order based on their Lumnis refresh date until all characters in that strategy have gotten their weekly experience bonus. When this occurs, the daemon will receive an empty response from the first strategy and evaluate the second (WeeklyResourceStrategy). This strategy will return the list of characters ordered by their Lumnis refresh date and remaining weekly resource required to cap.

##### Weekly Lumnis strategy

The [Gift of Lumnis](https://gswiki.play.net/Gift_of_Lumnis) lets characters earn a multiplier on their absorbed experience and thus it's desireable that when the bonus is active we're logging in with the characters and gaining experience. The rules around when Lumnis starts and how long it lasts get a bit complicated because the schedule can be moved and the actual bonus period doesn't start until your character earns experience. For our purposes:
1. The API will return the following possible values for `lumnis_2x` and `lumnis_3x`:
  - 7300 when the new Lumnis period has begun, as it's the maximum bonus for both 2x and 3x bonuses
  - A value between 0 and 7300 as the character earns experience and it counts against the bonus
  - 0 once that particular multipler has been worked through (eg., `lumnis_3x` can be 0 while `lumnis_2x` gets worked through). 0 for both fields indicates we've worked through the entire bonus for the week.
  - None indicates a character's Lumnis data has yet to be updated; these characters will be ignored in the strategy
1. The API will return the following possible values for `refresh`:
  - The UTC time of when the cycle refreshes if the character's bonus has started
  - None if the bonus has not yet started or if the data has yet to be sent

The TLDR is that when we see 7300/7300 and None for the refresh date, we know that character has a new Lumnis gift available.

How this is data is actually fetched can be seen in `get_lumnis_data` in `charman.lic`.

The TLDR for this strategy is we rank characters based on the following:
- Each character for which their Lumnis gift is available are equally viable and ranked the highest
- Next, characters that have started but not yet completed their bonus are ranked by their refresh date (ie., characters with less time to complete their bonus should be given priority)
- Characters that have completed their bonus are excluded from the results

##### Weekly resource strategy

Each Lumnis cycle, characters that have reached the necessary milestone can earn up to 50,000 points to their profession service. This value is straightforward:
- `weekly_resource` is an integer between 0 and 50000. That's the amount of resource a character has earned this cycle. A value of 50k signifies the character has capped their resource this cycle.
- when `weekly_resource` is None, this could mean the data was never sent or the character has not yet reached the milestone to earn resource towards their profession service.

The TLDR for this strategy is we rank characters based on the following:

- Characters that can earn weekly resource (ie., it's 0) but have not started their Lumnis cycle (`refresh` is None) are ranked the highest
- Next, characters that have started their Lumnis cycle are ranked by their refresh date (less time remaining is more priority)
- Characters that have completed their weekly resource (capped 50k) are excluded from the results
- Characters without a Lumnis refresh date set are excluded from the results

##### Daily login strategy

Given a list of characters, return a list containing characters whose last time online was before the most current daily reset (0000 eastern).

Caveat: Not sure if there's a more accurate way to do this. There is a message at logon or if you're already logged in that lets you know you've gotten the bonus for the day, but it's a one time thing. BOOST INFO gives you an ambiguous "You have been logged in for X days", but no way to tell from when exactly, and then it'd still be unclear when the 30 days cycles.

##### Favored character strategy

Fallback strategy; choose a favored character that gets the remainder of logon time.

TODO: Initially, I'll just hardcode these in the daemon's config. Eventually we can vend a way to alter them (config API, etc.). Until then, this attribute is defined in config.py's `CharData` and `CHARACTERS` is passed to the FavoredCharacter constructor.

##### Scheduled character strategy

TODO: This isn't something I plan on using, but if other people start to use this I could see it making sense. You define a list of characters and a schedule to keep them logged in during.

##### Edge cases

When characters are logged into the game they will likely (if we've automated that side correctly) start working through experience and thus their Lumnis and other attributes will change. This introduces several caveats we should account for.

###### Ping-Pong'ing

Let's say both character X and Y have their weekly Lumnis bonus available and we're using a strategy that simply looks at the value of Lumnis bonus remaining (the 2x/3x values). All things equal, the daemon logs in with the first character in our strategy result list, character X. X started to earn experience and so their Lumnis values fall. When this happens the naive Lumnis strategy will rank Y higher because they have a higher amount of Lumnis bonus they can earn. This results in a state where a character is active for a short time before being preempted by another and they continue to bump each other off.

Sometimes this is desirable. For example, characters earn a login bonus for logging in each day. We want to have a strategy that prioritizes logging in each character at least once so they earn this reward.

In other strategies, we should ensure that we're ranking characters on values that don't result in this behavior. In the WeeklyLumnisStrategy, we can work off the refresh date which will get set when we log in a character and they start their Lumnis bonus.

###### Strategy competition

For the layered strategy approach, it's important that strategies are capable of eventually yielding an empty list. If not, the remaining strategies will never be evaluated. The exception to this is the last strategy in the list, which can and should yield a result or the daemon will stop processing logon requests.

#### Login orchestrator

Given a list of character names and the list of strategies, 1) determine current character to login and 2) handle logging off/on. Each LoginOrchestrator is responsible for a single account and multiple orchestrators are instantiated by the daemon as required.

### Lich script

Should be added to Lich's autostart scripts. Periodically reads Lumnis and other data it sends back to the API server. When it receives a logoff request from the API server, handles getting the character into a safe state and quitting the game.

### API server

This is a very simple FastAPI server that stores and processes information the daemon and Lich script use. It has the following routes:
1. /characters/{name} - initial character creation, fetching character data
1. /characters/{name}/lumnis - populated from the Licht script, data about remaining Lumnis experience and weekly resource
1. /characters/{name}/pending-logout-requests - whether or not the Licht script should tidy things up and proceed with logging out

## Next steps
- We're using snake_case at the API interface, this should really be camelCase. Should make updates to the API and Lich script
- A configuration API (setting strategies, toggling the daemon's actions on/off, setting favored characters)
- A dashboard (shows currently logged in character and maybe some simple stats like xp/silver per hr)
- Eventually I want data persistence so I can useful stuff like metrics and looking back at previous login sessions, etc.
- Need a watchdog task for the API that cleans up login session data (ie., when the charman.lic script doesn't gracefully exit and set is_logged_in to false). If the (last_update + configurable timeout) < now and the state still shows as logged in, we should update to logged out.
- Parse login streak/bridge info?
- edge case: logging off with field experience > remaining lumnis bonus. if you do this it'd log you back in again. not a big deal for when we're running everything in an automated fashion, but i do this a lot when i play manually and it would make the strategy a tiny bit more efficient because of the offline absorption
- I spent a couple hours trying to get the enhanced encryption to work with gnome-keyring, libsecret-tools, dbus but there appears to be some extra trickery needed without x11. For now only plaintext|standard entry.yaml files will work and these get copied over from the data bind mount.
- 10 ports are mappable for the lich proxies. This is more than enough for my purposes. Supporting arbitrary ports means scaling horizontally and requires solving some additional problems (multiple containers means multiple lich data, etc.).

# TODO
- actual orchestration (mostly around logout)