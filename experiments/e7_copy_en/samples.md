# Samples

## en-US hits

| utterance | gold | pred |
|---|---|---|
| turn the lights off please | `iot_hue_lightoff()` | `iot_hue_lightoff()` |
| dim the lights in the hall | `iot_hue_lightdim(house_place="hall")` | `iot_hue_lightdim(house_place="hall")` |
| clean the flat | `iot_cleaning(house_place="flat")` | `iot_cleaning(house_place="flat")` |
| give me the status on my available memory | `general_quirky()` | `general_quirky()` |
| list most rated delivery options for chinese food | `takeaway_query(order_type="delivery", food_type="chinese")` | `takeaway_query(order_type="delivery", food_type="chinese")` |

## en-US misses

| utterance | gold | pred |
|---|---|---|
| make a room darker | `iot_hue_lightdim(house_place="room")` | `iot_hue_lightchange(color_type="room")` |
| cleaning is good dust is so bad do now your magic clean my carpet | `iot_cleaning(house_place="carpet")` | `general_quirky()` |
| i'd like to hear queen's barcelona | `play_music(artist_name="queen's", song_name="barcelona")` | `play_music(song_name="queen's barcelona")` |
| play me barcelona by queen | `play_music(song_name="barcelona", artist_name="queen")` | `play_music(song_name="barcelona barcelona", artist_name="queen")` |
| what's with my dinner order | `takeaway_query()` | `takeaway_query(meal_type="dinner")` |
| what's the weeks forecast | `weather_query(time="weeks")` | `weather_query(date="weeks")` |
| play hurts like heaven | `play_music(song_name="hurts like heaven")` | `play_music(artist_name="hurts like heaven")` |
| put on cannibal queen | `play_music(song_name="cannibal queen")` | `play_radio(radio_name="cannibal queen")` |
| loop this track | `music_settings(player_setting="loop")` | `play_music()` |
| set the volume to low | `audio_volume_down(change_amount="to low")` | `audio_volume_up(change_amount="to low")` |
