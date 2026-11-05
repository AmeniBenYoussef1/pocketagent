# B0 samples (dev)

## en-US hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| quiet | `audio_volume_mute()` | `audio_volume_mute()` | quiet | 1.00 |
| pink is all we need | `iot_hue_lightchange(color_type="pink")` | `iot_hue_lightchange(color_type="pink")` | change lights to pink | 0.46 |
| olly turn the lights off in the bedroom | `iot_hue_lightoff(house_place="bedroom")` | `iot_hue_lightoff(house_place="bedroom")` | turn the lights off in the bedroom | 0.94 |
| i want the status on my screen brightness | `general_quirky()` | `general_quirky()` | is the brightness of my screen running low | 0.67 |
| what's up olly | `general_greet()` | `general_greet()` | hey olly what's up | 0.86 |
| what's the time in australia | `datetime_query(place_name="australia")` | `datetime_query(place_name="australia")` | what is the time in australia right now | 0.83 |
| olly tell me the time in g. m. t. plus five | `datetime_convert(time_zone="g. m. t. plus five")` | `datetime_convert(time_zone="g. m. t. plus five")` | tell me the time in g. m. t. plus five | 0.95 |
| what alarms i have set | `alarm_query()` | `alarm_query()` | what alarms do i have set | 0.96 |
| tell me today's date | `datetime_query(date="today's")` | `datetime_query(date="today's")` | tell me the today's date | 0.98 |
| what date is it today | `datetime_query(date="today")` | `datetime_query(date="today")` | what date is today | 0.95 |

## en-US misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| wake me up at five am this week | `alarm_set(time="five am", date="this week")` | `alarm_set()` | wake me up at this time | 0.66 |
| and the darkness has fallen | `iot_hue_lighton()` | `weather_query(weather_descriptor="snow", place_name="maine", date="yesterday")` | how much snow has fallen in maine since yesterday | 0.40 |
| it's dirty here make some noise | `iot_cleaning()` | `play_music()` | make some noise | 0.71 |
| hoover the hallway | `iot_cleaning(house_place="hallway")` | `email_querycontact()` | where is hallway | 0.67 |
| cancel my seven am alarm | `alarm_remove(time="seven am")` | `alarm_remove(time="eight am")` | cancel my eight am alarm | 0.75 |
| tell me about my alarms | `alarm_query()` | `general_greet()` | olly tell me my alarms | 0.75 |
| i like senatra songs | `music_likeness(artist_name="senatra")` | `music_likeness()` | i like songs from | 0.59 |
| set lights brightness higher | `iot_hue_lightup()` | `iot_hue_lightdim()` | lower brightness of lights | 0.73 |
| could you order sushi for tonight dinner | `takeaway_order(food_type="sushi", timeofday="tonight", meal_type="dinner")` | `takeaway_order(food_type="sushi", meal_type="dinner")` | please order some sushi for dinner | 0.71 |
| what's the week's forecast | `weather_query(time="week's")` | `weather_query(date="this week's")` | show me this week's forecast | 0.82 |

## fr-FR hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| silence | `audio_volume_mute()` | `audio_volume_mute()` | silence | 1.00 |
| olly éteindre les lumières dans la chambre | `iot_hue_lightoff(house_place="chambre")` | `iot_hue_lightoff(house_place="chambre")` | éteindre les lumières dans ma chambre | 0.93 |
| je veux le statut sur la luminosité de mon écran | `general_quirky()` | `general_quirky()` | la luminosité de mon écran est-elle faible | 0.64 |
| quelle heure est-il en australie | `datetime_query(place_name="australie")` | `datetime_query(place_name="australie")` | quelle heure est-il maintenant en australie | 0.87 |
| quelles alarmes j'ai réglées | `alarm_query()` | `alarm_query()` | montre moi les alarmes que j'ai réglées | 0.83 |
| dis moi pour mes alarmes | `alarm_query()` | `alarm_query()` | mes alarmes | 0.80 |
| dis-moi la date d'aujourd'hui | `datetime_query(date="d'aujourd'hui")` | `datetime_query(date="d'aujourd'hui")` | dis moi la date d'aujourd'hui | 0.86 |
| quelle date est-il aujourd'hui | `datetime_query(date="aujourd'hui")` | `datetime_query(date="aujourd'hui")` | quelle date est aujourd'hui | 0.88 |
| quel temps fait-il cette semaine | `weather_query(date="cette semaine")` | `weather_query(date="cette semaine")` | quel temps fait-il cette semaine | 1.00 |
| dis-moi quel temps il fera cette semaine | `weather_query(date="cette semaine")` | `weather_query(date="cette semaine")` | quel temps fera-t-il cette semaine | 0.70 |

## fr-FR misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| réveille-moi à cinq heures du matin cette semaine | `alarm_set(time="cinq heures du matin", date="cette semaine")` | `alarm_set(time="six heures du matin")` | réveille-moi à six heures du matin | 0.74 |
| le rose est tout ce dont nous avons besoin | `iot_hue_lightchange(color_type="rose")` | `general_quirky()` | tout ce que j'ai besoin de savoir | 0.41 |
| et l'obscurité est tombée | `iot_hue_lighton()` | `general_quirky(date="aujourd'hui")` | je suis tombé au travail aujourd'hui | 0.28 |
| c'est sale ici fais du bruit | `iot_cleaning()` | `play_music()` | fais du bruit | 0.70 |
| passer l'aspirateur dans le couloir | `iot_cleaning(house_place="couloir")` | `iot_cleaning(house_place="maison")` | passer l'aspirateur dans la maison | 0.74 |
| quoi de neuf olly | `general_greet()` | `social_query()` | olly dis moi quoi de neuf | 0.90 |
| olly donne-moi l'heure en g. m. t. plus cinq | `datetime_convert(time_zone="g. m. t. plus cinq")` | `datetime_query()` | heure g. m. t. | 0.58 |
| annuler mon alarme de sept heures du matin | `alarm_remove(time="sept heures du matin")` | `alarm_set(time="sept heures du matin")` | régler une alarme pour sept heures du matin | 0.67 |
| j' aime les chansons de jacques brel | `music_likeness(artist_name="jacques brel")` | `play_music()` | jouer toutes les chansons jacques brel | 0.73 |
| régler la luminosité des lumières plus haut | `iot_hue_lightup()` | `iot_hue_lightdim()` | baisse la luminosité des lumières | 0.72 |

## ar-SA hits

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| هدوء | `audio_volume_mute()` | `audio_volume_mute()` | هدوء | 1.00 |
| وحل الظلام | `iot_hue_lighton()` | `iot_hue_lighton()` | الظلام يخوف هنا | 0.60 |
| المكان وسخ هنا ابدأ التنظيف | `iot_cleaning()` | `iot_cleaning()` | شغل مكنسة التنظيف | 0.51 |
| أبغى الحالة على سطوع الشاشة حقي | `general_quirky()` | `general_quirky()` | هل سطوع الشاشة حقي قليل | 0.70 |
| كم الوقت في السعودية | `datetime_query(place_name="السعودية")` | `datetime_query(place_name="السعودية")` | قل لي الوقت في السعودية | 0.88 |
| وش المنبهات اللي أنا حطيتها | `alarm_query()` | `alarm_query()` | وش المنبهات اللي حطيتها أنا | 1.00 |
| اخبريني عن منبهاتي | `alarm_query()` | `alarm_query()` | من فضلك اخبريني بالمنبهات القادمة | 0.59 |
| خل سطوع الإضاءة اعلى | `iot_hue_lightup()` | `iot_hue_lightup()` | خل الإضاءة أقوى | 0.55 |
| قل لي تاريخ اليوم | `datetime_query(date="اليوم")` | `datetime_query(date="اليوم")` | قل لي تاريخ اليوم | 1.00 |
| كم التاريخ اليوم | `datetime_query(date="اليوم")` | `datetime_query(date="اليوم")` | كم التاريخ اليوم | 1.00 |

## ar-SA misses

| utterance | gold | pred | nearest train utterance | sim |
|---|---|---|---|---|
| صحيني خمسة الفجر هذا الأسبوع | `alarm_set(time="خمسة الفجر", date="هذا الأسبوع")` | `alarm_set(time="أربعة الفجر")` | صحيني أربعة الفجر | 0.65 |
| بس نبي اللون الوردي | `iot_hue_lightchange(color_type="اللون الوردي")` | `play_music(artist_name="يعرف", song_name="اللون الوردي")` | ما حد يعرف ب اللون الوردي | 0.70 |
| طفي الاضواء بغرفة النوم حقي | `iot_hue_lightoff(house_place="بغرفة النوم")` | `iot_hue_lightoff(house_place="غرفة النوم")` | طفي نور غرفة النوم حقي | 0.57 |
| ممر | `iot_cleaning(house_place="ممر")` | `email_querycontact()` | وين الممر | 0.49 |
| كيفك اولي | `general_greet()` | `general_greet(date="اليوم")` | كيفك اليوم | 0.67 |
| قل لي أولي توقيت الرياض زائد خمسة | `datetime_convert(time_zone="توقيت الرياض")` | `datetime_query(place_name="الرياض")` | توقيت الرياض | 0.62 |
| كنسل منبه سبعة الصبح | `alarm_remove(time="سبعة الصبح")` | `alarm_set(time="سبعة الصبح")` | حط منبه على سبعة الصبح | 0.67 |
| تعجبني أغاني رابح | `music_likeness(artist_name="رابح")` | `recommendation_movies()` | اقترح عليا أفلام و أغاني راح تعجبني بس مو لازم تكون نفس اللي قلت انها تعجبني | 0.57 |
| عادي تطلب sushi عشان عشا الليلة | `takeaway_order(food_type="sushi", meal_type="عشا", timeofday="الليلة")` | `takeaway_order(meal_type="عشا", order_type="سفري", business_name="مطعم الطازج")` | عادي أطلب عشا سفري من مطعم الطازج | 0.35 |
| ما هي توقعات الاسبوع | `weather_query(time="الاسبوع")` | `weather_query(date="هذا الاسبوع")` | ما هي التوقعات هذا الاسبوع | 0.83 |
