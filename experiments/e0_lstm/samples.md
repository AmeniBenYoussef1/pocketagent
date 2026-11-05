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
| find my thai takeaways around grassmarket | `takeaway_query(food_type="thai", order_type="takeaways", place_name="grassmarket")` | `takeaway_query(food_type="thai", order_type="takeaways", place_name="<UNK>")` |
| i'd like to hear queen's barcelona | `play_music(artist_name="queen's", song_name="barcelona")` | `play_music(song_name="<UNK>", artist_name="tobymac")` |
| play me barcelona by queen | `play_music(song_name="barcelona", artist_name="queen")` | `play_music(song_name="i walk you", artist_name="tool")` |
| what's the weeks forecast | `weather_query(time="weeks")` | `weather_query(date="weekly")` |
| play hurts like heaven | `play_music(song_name="hurts like heaven")` | `play_music(song_name="<UNK> dragons")` |
| put on cannibal queen | `play_music(song_name="cannibal queen")` | `play_radio(radio_name="<UNK> <UNK>")` |
| loop this track | `music_settings(player_setting="loop")` | `audio_volume_up()` |
| set the volume to low | `audio_volume_down(change_amount="to low")` | `audio_volume_up(change_amount="to max")` |
| what time is it in las vegas | `datetime_query(place_name="las vegas")` | `datetime_query(place_name="boston florida")` |

## fr-FR hits

| utterance | gold | pred |
|---|---|---|
| éteigne les lumières s'il te plait | `iot_hue_lightoff()` | `iot_hue_lightoff()` |
| tamiser les lumières dans la salle | `iot_hue_lightdim(house_place="salle")` | `iot_hue_lightdim(house_place="salle")` |
| donne-moi l'état de ma mémoire disponible | `general_quirky()` | `general_quirky()` |
| liste les options de livraison les plus notées pour la nourriture chinois | `takeaway_query(order_type="livraison", food_type="chinois")` | `takeaway_query(order_type="livraison", food_type="chinois")` |
| trouve mes plats à emporter thaïlandais autour de la concorde | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` |

## fr-FR misses

| utterance | gold | pred |
|---|---|---|
| rendre une chambre foncée | `iot_hue_lightdim(house_place="chambre")` | `iot_hue_lightchange(color_type="<UNK>")` |
| nettoyer la télévision | `iot_cleaning(house_place="télévision")` | `iot_cleaning(device_type="télévision")` |
| le nettoyage est bon la poussière est si mauvaise fais maintenant ta magie nettoie mon tapis | `iot_cleaning(house_place="tapis")` | `general_quirky()` |
| qu'est-ce qu'il y a avec ma commande de dîner | `takeaway_query()` | `takeaway_query(food_type="sushi")` |
| quelles sont les prévisions de cette semaine | `weather_query(time="de cette semaine")` | `weather_query(date="de cette semaine")` |
| boucle cette piste | `music_settings(player_setting="boucle")` | `music_dislikeness()` |
| règle le volume sur le niveau bas | `audio_volume_down(change_amount="bas")` | `audio_volume_other()` |
| hé hé | `general_greet()` | `general_quirky()` |
| régler l'alarme demain à six heures du matin | `alarm_set(date="demain", time="six heures du matin")` | `alarm_set(date="demain", timeofday="matin", time="six")` |
| régler une alarme à six heures du matin | `alarm_set(time="six", timeofday="matin")` | `alarm_set(time="six heures du matin")` |

## ar-SA hits

| utterance | gold | pred |
|---|---|---|
| طفي اللمبات الله يسعدك | `iot_hue_lightoff()` | `iot_hue_lightoff()` |
| أعطني الحالة الخاصة فيني | `general_quirky()` | `general_quirky()` |
| شغل لعبد المجيد | `play_music(artist_name="لعبد المجيد")` | `play_music(artist_name="لعبد المجيد")` |
| ماهو اليوم | `datetime_query(date="اليوم")` | `datetime_query(date="اليوم")` |
| أي أغنية هذي | `music_query()` | `music_query()` |

## ar-SA misses

| utterance | gold | pred |
|---|---|---|
| وطي اللمبات في الممر | `iot_hue_lightdim(house_place="الممر")` | `iot_hue_lightdim()` |
| خلي الغرفة مظلمة أكثر | `iot_hue_lightdim(house_place="الغرفة")` | `iot_hue_lightoff(house_place="الغرفة <UNK>")` |
| نظف الشقة | `iot_cleaning(house_place="الشقة")` | `iot_cleaning(house_place="<UNK>")` |
| التنظيف جيد للغبار أمر سيء للغاية والآن قم بتنظيف سجادتي | `iot_cleaning(house_place="سجادتي")` | `general_quirky()` |
| حط بقائمة افضل المطاعم تقييم توصيل للاكل الهندي | `takeaway_query(order_type="توصيل", food_type="الهندي")` | `takeaway_order(business_type="المطاعم", food_type="<UNK>", order_type="يوصلوا")` |
| مطعم الملكي الملكي توصيل وجبتي البيتزا | `takeaway_query(place_name="مطعم الملكي", order_type="توصيل", food_type="البيتزا")` | `takeaway_order(business_name="مطعم الملكي", food_type="رقم <UNK>", order_type="توصيل")` |
| أريد أسمع سيناء الخاص بالملكة | `play_music(song_name="سيناء", artist_name="الخاص بالملكة")` | `play_podcasts(podcast_descriptor="الحلقة <UNK>")` |
| شغل لي شو المانع حق نجوى كرم | `play_music(song_name="شو المانع", artist_name="نجوى كرم")` | `play_music(song_name="اخر <UNK>", artist_name="راشد الماجد")` |
| ما الذي تعزفه الفرقة الآن | `music_query()` | `qa_factoid()` |
| إيش المشكلة مع طلب العشا حقي | `takeaway_query()` | `email_querycontact(personal_info="رقم", person="بدر")` |
