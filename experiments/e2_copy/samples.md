# Samples

## en-US hits

| utterance | gold | pred |
|---|---|---|
| turn the lights off please | `iot_hue_lightoff()` | `iot_hue_lightoff()` |
| dim the lights in the hall | `iot_hue_lightdim(house_place="hall")` | `iot_hue_lightdim(house_place="hall")` |
| make a room darker | `iot_hue_lightdim(house_place="room")` | `iot_hue_lightdim(house_place="room")` |
| clean the flat | `iot_cleaning(house_place="flat")` | `iot_cleaning(house_place="flat")` |
| give me the status on my available memory | `general_quirky()` | `general_quirky()` |

## en-US misses

| utterance | gold | pred |
|---|---|---|
| cleaning is good dust is so bad do now your magic clean my carpet | `iot_cleaning(house_place="carpet")` | `general_quirky()` |
| i'd like to hear queen's barcelona | `play_music(artist_name="queen's", song_name="barcelona")` | `play_music(artist_name="queen's barcelona")` |
| what's with my dinner order | `takeaway_query()` | `takeaway_query(meal_type="dinner")` |
| what's the weeks forecast | `weather_query(time="weeks")` | `weather_query(date="weeks")` |
| put on cannibal queen | `play_music(song_name="cannibal queen")` | `play_music(artist_name="cannibal queen")` |
| loop this track | `music_settings(player_setting="loop")` | `music_likeness()` |
| set the volume to low | `audio_volume_down(change_amount="to low")` | `audio_volume_up(change_amount="to low")` |
| hey hey | `general_greet()` | `general_quirky()` |
| did i set an alarm to wake up in the morning | `alarm_query(alarm_type="wake up", timeofday="morning")` | `alarm_query(timeofday="morning")` |
| tell me today's newspaper's headlines | `news_query(date="today's", media_type="newspaper's")` | `news_query(date="today's")` |

## fr-FR hits

| utterance | gold | pred |
|---|---|---|
| éteigne les lumières s'il te plait | `iot_hue_lightoff()` | `iot_hue_lightoff()` |
| tamiser les lumières dans la salle | `iot_hue_lightdim(house_place="salle")` | `iot_hue_lightdim(house_place="salle")` |
| nettoyer la télévision | `iot_cleaning(house_place="télévision")` | `iot_cleaning(house_place="télévision")` |
| liste les options de livraison les plus notées pour la nourriture chinois | `takeaway_query(order_type="livraison", food_type="chinois")` | `takeaway_query(order_type="livraison", food_type="chinois")` |
| trouve mes plats à emporter thaïlandais autour de la concorde | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` |

## fr-FR misses

| utterance | gold | pred |
|---|---|---|
| rendre une chambre foncée | `iot_hue_lightdim(house_place="chambre")` | `iot_hue_lightchange(house_place="chambre", color_type="foncée")` |
| le nettoyage est bon la poussière est si mauvaise fais maintenant ta magie nettoie mon tapis | `iot_cleaning(house_place="tapis")` | `general_quirky()` |
| donne-moi l'état de ma mémoire disponible | `general_quirky()` | `music_query()` |
| jouer moi jacques brel ne me quitte pas | `play_music()` | `play_music(artist_name="jacques brel", song_name="ne me quitte pas")` |
| qu'est-ce qu'il y a avec ma commande de dîner | `takeaway_query()` | `takeaway_query(meal_type="dîner")` |
| quelles sont les prévisions de cette semaine | `weather_query(time="de cette semaine")` | `weather_query(date="de cette semaine")` |
| boucle cette piste | `music_settings(player_setting="boucle")` | `music_dislikeness()` |
| règle le volume sur le niveau bas | `audio_volume_down(change_amount="bas")` | `audio_volume_down()` |
| j'aime écouter le jazz | `play_music(music_genre="jazz")` | `music_likeness(music_genre="jazz")` |
| hé hé | `general_greet()` | `general_quirky()` |

## ar-SA hits

| utterance | gold | pred |
|---|---|---|
| نظف الشقة | `iot_cleaning(house_place="الشقة")` | `iot_cleaning(house_place="الشقة")` |
| شغل أهواك | `play_music(song_name="أهواك")` | `play_music(song_name="أهواك")` |
| شغل لعبد المجيد | `play_music(artist_name="لعبد المجيد")` | `play_music(artist_name="لعبد المجيد")` |
| ماهو اليوم | `datetime_query(date="اليوم")` | `datetime_query(date="اليوم")` |
| أي أغنية هذي | `music_query()` | `music_query()` |

## ar-SA misses

| utterance | gold | pred |
|---|---|---|
| طفي اللمبات الله يسعدك | `iot_hue_lightoff()` | `iot_hue_lightoff(device_type="اللمبات", change_amount="الله يسعدك")` |
| وطي اللمبات في الممر | `iot_hue_lightdim(house_place="الممر")` | `iot_hue_lightdim()` |
| خلي الغرفة مظلمة أكثر | `iot_hue_lightdim(house_place="الغرفة")` | `iot_hue_lightoff(house_place="الغرفة", change_amount="مظلمة")` |
| التنظيف جيد للغبار أمر سيء للغاية والآن قم بتنظيف سجادتي | `iot_cleaning(house_place="سجادتي")` | `general_quirky()` |
| أعطني الحالة الخاصة فيني | `general_quirky()` | `social_query()` |
| حط بقائمة افضل المطاعم تقييم توصيل للاكل الهندي | `takeaway_query(order_type="توصيل", food_type="الهندي")` | `music_likeness(business_type="المطاعم", order_type="توصيل")` |
| مطعم الملكي الملكي توصيل وجبتي البيتزا | `takeaway_query(place_name="مطعم الملكي", order_type="توصيل", food_type="البيتزا")` | `takeaway_order(business_name="مطعم الملكي", order_type="توصيل", food_type="البيتزا")` |
| أريد أسمع سيناء الخاص بالملكة | `play_music(song_name="سيناء", artist_name="الخاص بالملكة")` | `play_music(music_genre="سيناء", artist_name="بالملكة")` |
| شغل لي شو المانع حق نجوى كرم | `play_music(song_name="شو المانع", artist_name="نجوى كرم")` | `play_music(artist_name="نجوى كرم")` |
| ما الذي تعزفه الفرقة الآن | `music_query()` | `qa_factoid()` |
