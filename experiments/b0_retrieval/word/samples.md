# B0 samples (dev)

## en-US hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| turn the lights off please | `iot_hue_lightoff()` | `iot_hue_lightoff()` | turn the lights off now | 0.64 |
| dim the lights in the hall | `iot_hue_lightdim(house_place="hall")` | `iot_hue_lightdim(house_place="hall")` | olly dim the lights in the hall | 0.89 |
| clean the flat | `iot_cleaning(house_place="flat")` | `iot_cleaning(house_place="flat")` | olly clean the flat | 0.85 |
| list most rated delivery options for chinese food | `takeaway_query(order_type="delivery", food_type="chinese")` | `takeaway_query(order_type="delivery", food_type="chinese")` | olly list most rated delivery options for chinese food | 0.95 |
| find my thai takeaways around grassmarket | `takeaway_query(food_type="thai", order_type="takeaways", place_name="grassmarket")` | `takeaway_query(food_type="thai", order_type="takeaways", place_name="grassmarket")` | find my thai takeaways around grassmarket | 1.00 |
| what's the band is playing now | `music_query()` | `music_query()` | tell me what is song is playing now | 0.46 |
| what's with my dinner order | `takeaway_query()` | `takeaway_query()` | what's up with my order | 0.44 |
| play some david bowie | `play_music(artist_name="david bowie")` | `play_music(artist_name="david bowie")` | play david bowie | 0.73 |
| which song is that | `music_query()` | `music_query()` | which song is this | 0.74 |
| volume up | `audio_volume_up()` | `audio_volume_up()` | volume up | 1.00 |

## en-US misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| make a room darker | `iot_hue_lightdim(house_place="room")` | `lists_createoradd()` | make a list | 0.46 |
| cleaning is good dust is so bad do now your magic clean my carpet | `iot_cleaning(house_place="carpet")` | `calendar_remove()` | clean my calendar | 0.35 |
| give me the status on my available memory | `general_quirky()` | `datetime_query()` | give me the time | 0.39 |
| i'd like to hear queen's barcelona | `play_music(artist_name="queen's", song_name="barcelona")` | `play_music(song_name="motown")` | i'd like to hear some motown | 0.59 |
| play me barcelona by queen | `play_music(song_name="barcelona", artist_name="queen")` | `play_music()` | play me a song | 0.31 |
| what's the weeks forecast | `weather_query(time="weeks")` | `weather_query(date="this weeks")` | this weeks weather forecast | 0.44 |
| play hurts like heaven | `play_music(song_name="hurts like heaven")` | `qa_definition(definition_word="heaven")` | describe heaven | 0.51 |
| put on cannibal queen | `play_music(song_name="cannibal queen")` | `play_radio()` | put on the radio | 0.52 |
| loop this track | `music_settings(player_setting="loop")` | `music_query()` | tell me the singer of this track | 0.46 |
| set the volume to low | `audio_volume_down(change_amount="to low")` | `audio_volume_down()` | low the volume | 0.56 |

## fr-FR hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| éteigne les lumières s'il te plait | `iot_hue_lightoff()` | `iot_hue_lightoff()` | éteindre les lumières s'il te plait | 0.74 |
| tamiser les lumières dans la salle | `iot_hue_lightdim(house_place="salle")` | `iot_hue_lightdim(house_place="salle")` | olly tamiser les lumières dans la salle | 0.88 |
| liste les options de livraison les plus notées pour la nourriture chinois | `takeaway_query(order_type="livraison", food_type="chinois")` | `takeaway_query(order_type="livraison", food_type="chinois")` | les options de livraison les plus notées pour du chinois | 0.82 |
| trouve mes plats à emporter thaïlandais autour de la concorde | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` | trouve mes plats à emporter thaïlandais autour de la concorde | 1.00 |
| j'aimerais écouter ne me quitte pas de jacques brel | `play_music(song_name="ne me quitte pas", artist_name="jacques brel")` | `play_music(song_name="ne me quitte pas", artist_name="jacques brel")` | ne me quitte pas de jacques brel | 0.81 |
| quel est le groupe qui chante maintenant | `music_query()` | `music_query()` | qui chante | 0.56 |
| joue ne me quitte pas | `play_music(song_name="ne me quitte pas")` | `play_music(song_name="ne me quitte pas")` | joue ne me quitte pas | 1.00 |
| jouer la chanson ne me quitte pas | `play_music()` | `play_music()` | jouer la chanson ne me quitte pas | 1.00 |
| joue un peu de jaques brel | `play_music(artist_name="jaques brel")` | `play_music(artist_name="jaques brel")` | joue la playlist de jaques brel | 0.61 |
| quel jour sommes-nous aujourd'hui | `datetime_query(date="aujourd'hui")` | `datetime_query(date="aujourd'hui")` | quel jour sommes-nous aujourd'hui | 1.00 |

## fr-FR misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| rendre une chambre foncée | `iot_hue_lightdim(house_place="chambre")` | `iot_hue_lightdim()` | j'aimerais une chambre moins lumineuse | 0.44 |
| nettoyer la télévision | `iot_cleaning(house_place="télévision")` | `general_quirky()` | télévision | 0.47 |
| le nettoyage est bon la poussière est si mauvaise fais maintenant ta magie nettoie mon tapis | `iot_cleaning(house_place="tapis")` | `iot_cleaning(device_type="aspirateur")` | enlever la poussière avec un aspirateur | 0.23 |
| donne-moi l'état de ma mémoire disponible | `general_quirky()` | `takeaway_query()` | vérifie l'état de ma commande | 0.58 |
| jouer moi jacques brel ne me quitte pas | `play_music()` | `play_music(artist_name="jacques brel", song_name="ne me quitte pas")` | joue jacques brel ne me quitte pas | 0.78 |
| qu'est-ce qu'il y a avec ma commande de dîner | `takeaway_query()` | `general_quirky(meal_type="dîner")` | qu'est-ce qu'il y a pour le dîner | 0.51 |
| quelles sont les prévisions de cette semaine | `weather_query(time="de cette semaine")` | `weather_query(date="de cette semaine")` | montre moi les prévisions de cette semaine | 0.73 |
| boucle cette piste | `music_settings(player_setting="boucle")` | `music_settings()` | augmente le volume de de cette piste courente | 0.42 |
| règle le volume sur le niveau bas | `audio_volume_down(change_amount="bas")` | `audio_volume_other()` | règle le son | 0.47 |
| j'aime écouter le jazz | `play_music(music_genre="jazz")` | `music_likeness(music_genre="jazz")` | j'aime le jazz | 0.59 |

## ar-SA hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| طفي اللمبات الله يسعدك | `iot_hue_lightoff()` | `iot_hue_lightoff()` | طفي اللمبات | 0.66 |
| نظف الشقة | `iot_cleaning(house_place="الشقة")` | `iot_cleaning(house_place="الشقة")` | olly نظف الشقة | 0.82 |
| شغل لعبد المجيد | `play_music(artist_name="لعبد المجيد")` | `play_music(artist_name="لعبد المجيد")` | أبغى أسمع لعبد المجيد | 0.68 |
| ماهو اليوم | `datetime_query(date="اليوم")` | `datetime_query(date="اليوم")` | ماهو تاريخ اليوم | 0.58 |
| أي أغنية هذي | `music_query()` | `music_query()` | أغنية هذي | 0.78 |
| olly أحب أسمع موسيقى jazz | `play_music(music_genre="jazz")` | `play_music(music_genre="jazz")` | شغل موسيقى jazz | 0.56 |
| سلام سلام | `general_greet()` | `general_greet()` | سلام عليكم | 0.45 |
| ارفع الصوت | `audio_volume_up()` | `audio_volume_up()` | ارفع الصوت | 1.00 |
| طفي الفيش الذكي | `iot_wemo_off(device_type="الفيش الذكي")` | `iot_wemo_off(device_type="الفيش الذكي")` | طفي الفيش الذكي | 1.00 |
| شغل أغنية من مفضلاتي | `play_music()` | `play_music()` | شغل أغنية | 0.60 |

## ar-SA misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| وطي اللمبات في الممر | `iot_hue_lightdim(house_place="الممر")` | `iot_hue_lightdim(house_place="بغرفة المجلس")` | وطي اللمبات شوي بغرفة المجلس | 0.39 |
| خلي الغرفة مظلمة أكثر | `iot_hue_lightdim(house_place="الغرفة")` | `iot_hue_lightchange(house_place="الغرفة", color_type="زرقا")` | خلي الغرفة زرقا | 0.67 |
| التنظيف جيد للغبار أمر سيء للغاية والآن قم بتنظيف سجادتي | `iot_cleaning(house_place="سجادتي")` | `general_quirky()` | هاد المحل جيد ام سيء | 0.25 |
| أعطني الحالة الخاصة فيني | `general_quirky()` | `social_post()` | غيري الحالة | 0.28 |
| حط بقائمة افضل المطاعم تقييم توصيل للاكل الهندي | `takeaway_query(order_type="توصيل", food_type="الهندي")` | `takeaway_order(order_type="توصيل")` | توصيل | 0.33 |
| مطعم الملكي الملكي توصيل وجبتي البيتزا | `takeaway_query(place_name="مطعم الملكي", order_type="توصيل", food_type="البيتزا")` | `takeaway_order(business_name="مطعم الملكي")` | مطعم الملكي | 0.75 |
| أريد أسمع سيناء الخاص بالملكة | `play_music(song_name="سيناء", artist_name="الخاص بالملكة")` | `play_audiobook(media_type="كتاب أغاني")` | أريد أسمع كتاب أغاني الخاص بي | 0.49 |
| شغل لي شو المانع حق نجوى كرم | `play_music(song_name="شو المانع", artist_name="نجوى كرم")` | `play_music(artist_name="نجوى كرم")` | شغل موسيقى نجوى كرم | 0.56 |
| ما الذي تعزفه الفرقة الآن | `music_query()` | `qa_definition()` | ما الذي يعنيه هذا | 0.48 |
| إيش المشكلة مع طلب العشا حقي | `takeaway_query()` | `calendar_set(event_name="خطة العشا")` | خطة العشا حقي | 0.47 |
