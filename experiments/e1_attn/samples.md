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
| make a room darker | `iot_hue_lightdim(house_place="room")` | `iot_hue_lightdim(change_amount="to sixty")` |
| cleaning is good dust is so bad do now your magic clean my carpet | `iot_cleaning(house_place="carpet")` | `general_quirky()` |
| find my thai takeaways around grassmarket | `takeaway_query(food_type="thai", order_type="takeaways", place_name="grassmarket")` | `takeaway_query(food_type="thai", order_type="takeaways", place_name="<UNK>")` |
| i'd like to hear queen's barcelona | `play_music(artist_name="queen's", song_name="barcelona")` | `play_music(song_name="<UNK>", artist_name="<UNK>")` |
| play me barcelona by queen | `play_music(song_name="barcelona", artist_name="queen")` | `play_music(song_name="get يمشي", artist_name="zedd")` |
| what's with my dinner order | `takeaway_query()` | `takeaway_query(meal_type="dinner")` |
| what's the weeks forecast | `weather_query(time="weeks")` | `weather_query()` |
| play hurts like heaven | `play_music(song_name="hurts like heaven")` | `play_music(artist_name="<UNK> <UNK>", song_name="running to <UNK>")` |
| put on cannibal queen | `play_music(song_name="cannibal queen")` | `iot_wemo_on(device_type="<UNK>")` |
| loop this track | `music_settings(player_setting="loop")` | `music_likeness()` |

## fr-FR hits

| utterance | gold | pred |
|---|---|---|
| tamiser les lumières dans la salle | `iot_hue_lightdim(house_place="salle")` | `iot_hue_lightdim(house_place="salle")` |
| nettoyer la télévision | `iot_cleaning(house_place="télévision")` | `iot_cleaning(house_place="télévision")` |
| liste les options de livraison les plus notées pour la nourriture chinois | `takeaway_query(order_type="livraison", food_type="chinois")` | `takeaway_query(order_type="livraison", food_type="chinois")` |
| trouve mes plats à emporter thaïlandais autour de la concorde | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` |
| quel est le groupe qui chante maintenant | `music_query()` | `music_query()` |

## fr-FR misses

| utterance | gold | pred |
|---|---|---|
| éteigne les lumières s'il te plait | `iot_hue_lightoff()` | `iot_hue_lightup()` |
| rendre une chambre foncée | `iot_hue_lightdim(house_place="chambre")` | `iot_hue_lightchange(color_type="<UNK>")` |
| le nettoyage est bon la poussière est si mauvaise fais maintenant ta magie nettoie mon tapis | `iot_cleaning(house_place="tapis")` | `general_quirky()` |
| donne-moi l'état de ma mémoire disponible | `general_quirky()` | `music_likeness()` |
| j'aimerais écouter ne me quitte pas de jacques brel | `play_music(song_name="ne me quitte pas", artist_name="jacques brel")` | `play_music()` |
| jouer moi jacques brel ne me quitte pas | `play_music()` | `play_music(artist_name="jacques brel", song_name="ne me quitte pas")` |
| qu'est-ce qu'il y a avec ma commande de dîner | `takeaway_query()` | `takeaway_query(meal_type="dîner")` |
| quelles sont les prévisions de cette semaine | `weather_query(time="de cette semaine")` | `weather_query(date="de cette semaine")` |
| joue ne me quitte pas | `play_music(song_name="ne me quitte pas")` | `play_music()` |
| boucle cette piste | `music_settings(player_setting="boucle")` | `music_likeness()` |

## ar-SA hits

| utterance | gold | pred |
|---|---|---|
| طفي اللمبات الله يسعدك | `iot_hue_lightoff()` | `iot_hue_lightoff()` |
| شغل لعبد المجيد | `play_music(artist_name="لعبد المجيد")` | `play_music(artist_name="لعبد المجيد")` |
| أي أغنية هذي | `music_query()` | `music_query()` |
| أريد أسمع jazz | `play_music(music_genre="jazz")` | `play_music(music_genre="jazz")` |
| olly أحب أسمع موسيقى jazz | `play_music(music_genre="jazz")` | `play_music(music_genre="jazz")` |

## ar-SA misses

| utterance | gold | pred |
|---|---|---|
| وطي اللمبات في الممر | `iot_hue_lightdim(house_place="الممر")` | `iot_hue_lightdim(house_place="البيت")` |
| خلي الغرفة مظلمة أكثر | `iot_hue_lightdim(house_place="الغرفة")` | `iot_hue_lightup(house_place="الغرفة <UNK>")` |
| نظف الشقة | `iot_cleaning(house_place="الشقة")` | `iot_cleaning(house_place="<UNK>")` |
| التنظيف جيد للغبار أمر سيء للغاية والآن قم بتنظيف سجادتي | `iot_cleaning(house_place="سجادتي")` | `general_quirky()` |
| أعطني الحالة الخاصة فيني | `general_quirky()` | `general_joke(joke_type="أحسن")` |
| حط بقائمة افضل المطاعم تقييم توصيل للاكل الهندي | `takeaway_query(order_type="توصيل", food_type="الهندي")` | `takeaway_order(business_type="المطاعم", food_type="<UNK>", meal_type="<UNK>")` |
| مطعم الملكي الملكي توصيل وجبتي البيتزا | `takeaway_query(place_name="مطعم الملكي", order_type="توصيل", food_type="البيتزا")` | `takeaway_order(business_type="مطعم", food_type="بيتزا بيبروني <UNK>", business_name="مطعم <UNK>")` |
| أريد أسمع سيناء الخاص بالملكة | `play_music(song_name="سيناء", artist_name="الخاص بالملكة")` | `play_music(artist_name="michel <UNK>")` |
| شغل لي شو المانع حق نجوى كرم | `play_music(song_name="شو المانع", artist_name="نجوى كرم")` | `play_music(artist_name="انغامي القرني")` |
| ما الذي تعزفه الفرقة الآن | `music_query()` | `qa_definition()` |
