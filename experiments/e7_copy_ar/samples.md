# Samples

## ar-SA hits

| utterance | gold | pred |
|---|---|---|
| طفي اللمبات الله يسعدك | `iot_hue_lightoff()` | `iot_hue_lightoff()` |
| وطي اللمبات في الممر | `iot_hue_lightdim(house_place="الممر")` | `iot_hue_lightdim(house_place="الممر")` |
| نظف الشقة | `iot_cleaning(house_place="الشقة")` | `iot_cleaning(house_place="الشقة")` |
| شغل لي شو المانع حق نجوى كرم | `play_music(song_name="شو المانع", artist_name="نجوى كرم")` | `play_music(song_name="شو المانع", artist_name="نجوى كرم")` |
| شغل لعبد المجيد | `play_music(artist_name="لعبد المجيد")` | `play_music(artist_name="لعبد المجيد")` |

## ar-SA misses

| utterance | gold | pred |
|---|---|---|
| خلي الغرفة مظلمة أكثر | `iot_hue_lightdim(house_place="الغرفة")` | `iot_hue_lightup(house_place="الغرفة")` |
| التنظيف جيد للغبار أمر سيء للغاية والآن قم بتنظيف سجادتي | `iot_cleaning(house_place="سجادتي")` | `social_post()` |
| أعطني الحالة الخاصة فيني | `general_quirky()` | `social_post()` |
| حط بقائمة افضل المطاعم تقييم توصيل للاكل الهندي | `takeaway_query(order_type="توصيل", food_type="الهندي")` | `takeaway_order(food_type="المطاعم", order_type="توصيل")` |
| مطعم الملكي الملكي توصيل وجبتي البيتزا | `takeaway_query(place_name="مطعم الملكي", order_type="توصيل", food_type="البيتزا")` | `takeaway_order(business_name="مطعم الملكي الملكي", food_type="توصيل")` |
| أريد أسمع سيناء الخاص بالملكة | `play_music(song_name="سيناء", artist_name="الخاص بالملكة")` | `play_music(artist_name="سيناء")` |
| ما الذي تعزفه الفرقة الآن | `music_query()` | `datetime_query()` |
| إيش المشكلة مع طلب العشا حقي | `takeaway_query()` | `cooking_recipe()` |
| ما هي توقعات الأسابيع | `weather_query(time="الأسابيع")` | `weather_query()` |
| شغلل كان يا مكان | `play_music(song_name="كان يا مكان")` | `general_quirky()` |
