# B0 samples (dev)

## en-US hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| turn the lights off please | `iot_hue_lightoff()` | `iot_hue_lightoff()` | please turn off the lights | 1.00 |
| dim the lights in the hall | `iot_hue_lightdim(house_place="hall")` | `iot_hue_lightdim(house_place="hall")` | olly dim the lights in the hall | 0.92 |
| clean the flat | `iot_cleaning(house_place="flat")` | `iot_cleaning(house_place="flat")` | olly clean the flat | 0.91 |
| list most rated delivery options for chinese food | `takeaway_query(order_type="delivery", food_type="chinese")` | `takeaway_query(order_type="delivery", food_type="chinese")` | most rated delivery options for chinese food | 0.98 |
| find my thai takeaways around grassmarket | `takeaway_query(food_type="thai", order_type="takeaways", place_name="grassmarket")` | `takeaway_query(food_type="thai", order_type="takeaways", place_name="grassmarket")` | find my thai takeaways around grassmarket | 1.00 |
| what's the band is playing now | `music_query()` | `music_query()` | what's playing | 0.75 |
| play some david bowie | `play_music(artist_name="david bowie")` | `play_music(artist_name="david bowie")` | play david bowie | 0.94 |
| what's the day today | `datetime_query(date="today")` | `datetime_query(date="today")` | what's today | 0.90 |
| which song is that | `music_query()` | `music_query()` | which song is this | 0.84 |
| i like to listen to jazz | `play_music(music_genre="jazz")` | `play_music(music_genre="jazz")` | i want to listen jazz | 0.82 |

## en-US misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| make a room darker | `iot_hue_lightdim(house_place="room")` | `iot_hue_lightdim()` | darker lights please | 0.59 |
| cleaning is good dust is so bad do now your magic clean my carpet | `iot_cleaning(house_place="carpet")` | `iot_cleaning(house_place="carpets")` | clean the carpets | 0.49 |
| give me the status on my available memory | `general_quirky()` | `lists_query()` | the available lists | 0.57 |
| i'd like to hear queen's barcelona | `play_music(artist_name="queen's", song_name="barcelona")` | `weather_query(weather_descriptor="raining", place_name="barcelona")` | is it raining in barcelona | 0.56 |
| play me barcelona by queen | `play_music(song_name="barcelona", artist_name="queen")` | `weather_query(weather_descriptor="raining", place_name="barcelona")` | is it raining in barcelona | 0.65 |
| what's with my dinner order | `takeaway_query()` | `general_quirky(meal_type="dinner")` | what's for dinner | 0.75 |
| what's the weeks forecast | `weather_query(time="weeks")` | `weather_query(date="this week")` | what's the forecast for this week | 0.79 |
| play hurts like heaven | `play_music(song_name="hurts like heaven")` | `qa_definition(definition_word="heaven")` | describe heaven | 0.44 |
| put on cannibal queen | `play_music(song_name="cannibal queen")` | `music_likeness(artist_name="queen")` | my favorite music band is queen | 0.41 |
| loop this track | `music_settings(player_setting="loop")` | `music_query()` | tell me the song track | 0.48 |

## fr-FR hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| éteigne les lumières s'il te plait | `iot_hue_lightoff()` | `iot_hue_lightoff()` | s'il te plait éteint les lumières s'il te plait | 0.71 |
| tamiser les lumières dans la salle | `iot_hue_lightdim(house_place="salle")` | `iot_hue_lightdim(house_place="salle")` | olly tamiser les lumières dans la salle | 0.94 |
| liste les options de livraison les plus notées pour la nourriture chinois | `takeaway_query(order_type="livraison", food_type="chinois")` | `takeaway_query(order_type="livraison", food_type="chinois")` | les options de livraison les plus notées pour du chinois | 0.88 |
| trouve mes plats à emporter thaïlandais autour de la concorde | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` | trouve mes plats à emporter thaïlandais autour de la concorde | 1.00 |
| j'aimerais écouter ne me quitte pas de jacques brel | `play_music(song_name="ne me quitte pas", artist_name="jacques brel")` | `play_music(song_name="ne me quitte pas", artist_name="jacques brel")` | écoute par ne me quitte pas jacques brel | 0.79 |
| joue ne me quitte pas | `play_music(song_name="ne me quitte pas")` | `play_music(song_name="ne me quitte pas")` | joue ne me quitte pas | 1.00 |
| jouer la chanson ne me quitte pas | `play_music()` | `play_music()` | jouer la chanson ne me quitte pas | 1.00 |
| joue un peu de jaques brel | `play_music(artist_name="jaques brel")` | `play_music(artist_name="jaques brel")` | joue des chants de jaques brel | 0.77 |
| quel jour sommes-nous aujourd'hui | `datetime_query(date="aujourd'hui")` | `datetime_query(date="aujourd'hui")` | quel jour sommes-nous aujourd'hui | 1.00 |
| qu'elle est cette chanson | `music_query()` | `music_query()` | quelle est cette chanson | 0.72 |

## fr-FR misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| rendre une chambre foncée | `iot_hue_lightdim(house_place="chambre")` | `iot_hue_lightchange(house_place="chambre", color_type="bleue")` | rendre la chambre bleue | 0.53 |
| nettoyer la télévision | `iot_cleaning(house_place="télévision")` | `general_quirky()` | télévision | 0.74 |
| le nettoyage est bon la poussière est si mauvaise fais maintenant ta magie nettoie mon tapis | `iot_cleaning(house_place="tapis")` | `iot_cleaning(device_type="nettoyeur")` | nettoyer la poussière puis sur le nettoyeur | 0.48 |
| donne-moi l'état de ma mémoire disponible | `general_quirky()` | `iot_wemo_on()` | rendre la prise disponible pour moi | 0.48 |
| jouer moi jacques brel ne me quitte pas | `play_music()` | `play_music(artist_name="jacques brel", song_name="ne me quitte pas")` | joue jacques brel ne me quitte pas | 0.93 |
| quel est le groupe qui chante maintenant | `music_query()` | `weather_query()` | quel est le temps maintenant | 0.57 |
| qu'est-ce qu'il y a avec ma commande de dîner | `takeaway_query()` | `general_quirky(meal_type="dîner")` | qu'est-ce qu'il y a pour le dîner | 0.79 |
| quelles sont les prévisions de cette semaine | `weather_query(time="de cette semaine")` | `weather_query(date="cette semaine")` | quelles sont les prévisions pour cette semaine | 0.97 |
| boucle cette piste | `music_settings(player_setting="boucle")` | `music_settings(player_setting="en boucle")` | mets la chanson en cours en boucle | 0.55 |
| règle le volume sur le niveau bas | `audio_volume_down(change_amount="bas")` | `audio_volume_other()` | niveau du volume | 0.65 |

## ar-SA hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| نظف الشقة | `iot_cleaning(house_place="الشقة")` | `iot_cleaning(house_place="الشقة")` | olly نظف الشقة | 0.89 |
| شغل لعبد المجيد | `play_music(artist_name="لعبد المجيد")` | `play_music(artist_name="لعبد المجيد")` | أبغى أسمع لعبد المجيد | 0.76 |
| ماهو اليوم | `datetime_query(date="اليوم")` | `datetime_query(date="اليوم")` | ماهو تاريخ اليوم | 0.78 |
| أي أغنية هذي | `music_query()` | `music_query()` | أغنية هذي | 0.94 |
| olly أحب أسمع موسيقى jazz | `play_music(music_genre="jazz")` | `play_music(music_genre="jazz")` | شغل موسيقى jazz | 0.71 |
| ارفع الصوت | `audio_volume_up()` | `audio_volume_up()` | ارفع الصوت | 1.00 |
| هل تمطر في الخارج | `weather_query(weather_descriptor="تمطر")` | `weather_query(weather_descriptor="تمطر")` | هل تمطر | 0.65 |
| كيف هو الطقس في مدينة مكة | `weather_query(place_name="مكة")` | `weather_query(place_name="مكة")` | كيف هو الطقس في مكة | 0.80 |
| طفي الفيش الذكي | `iot_wemo_off(device_type="الفيش الذكي")` | `iot_wemo_off(device_type="الفيش الذكي")` | طفي الفيش الذكي | 1.00 |
| أريد اسمع موسيقى بوب | `play_music(music_genre="بوب")` | `play_music(music_genre="بوب")` | شغلي شوية موسيقى بوب | 0.57 |

## ar-SA misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| طفي اللمبات الله يسعدك | `iot_hue_lightoff()` | `iot_hue_lightoff(house_place="المطبخ")` | طف اللمبات في المطبخ الله يسعدك | 0.81 |
| وطي اللمبات في الممر | `iot_hue_lightdim(house_place="الممر")` | `email_querycontact()` | وين الممر | 0.59 |
| خلي الغرفة مظلمة أكثر | `iot_hue_lightdim(house_place="الغرفة")` | `iot_hue_lightchange(house_place="الغرفة", color_type="زرقا")` | خلي الغرفة زرقا | 0.48 |
| التنظيف جيد للغبار أمر سيء للغاية والآن قم بتنظيف سجادتي | `iot_cleaning(house_place="سجادتي")` | `lists_createoradd(list_name="قائمة التنظيف")` | ظيف تنظيف الكلب أول شي في قائمة التنظيف | 0.43 |
| أعطني الحالة الخاصة فيني | `general_quirky()` | `weather_query(place_name="عسير")` | أعطني حالة الطقس في عسير | 0.40 |
| حط بقائمة افضل المطاعم تقييم توصيل للاكل الهندي | `takeaway_query(order_type="توصيل", food_type="الهندي")` | `takeaway_query(food_type="الحجازي", order_type="يوصلوا")` | olly وش المطاعم الاكثر تقييم للاكل الحجازي و يوصلوا | 0.45 |
| مطعم الملكي الملكي توصيل وجبتي البيتزا | `takeaway_query(place_name="مطعم الملكي", order_type="توصيل", food_type="البيتزا")` | `takeaway_order(business_name="مطعم الملكي")` | مطعم الملكي | 0.71 |
| أريد أسمع سيناء الخاص بالملكة | `play_music(song_name="سيناء", artist_name="الخاص بالملكة")` | `play_audiobook(media_type="كتاب أغاني")` | أريد أسمع كتاب أغاني الخاص بي | 0.48 |
| شغل لي شو المانع حق نجوى كرم | `play_music(song_name="شو المانع", artist_name="نجوى كرم")` | `play_music(artist_name="نجوى كرم")` | شغل موسيقى نجوى كرم | 0.67 |
| ما الذي تعزفه الفرقة الآن | `music_query()` | `datetime_query()` | ما هو الوقت الآن | 0.31 |
