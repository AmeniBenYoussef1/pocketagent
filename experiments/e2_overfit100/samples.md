# Samples

## en-US hits

| utterance | gold | pred |
|---|---|---|
| delete shopping list | `lists_remove(list_name="shopping")` | `lists_remove(list_name="shopping")` |
| what a wonderful song can you save what i just said for me | `music_likeness()` | `music_likeness()` |
| what is the dollar equivalent in pesos | `qa_currency(currency_name="dollar", currency_name="pesos")` | `qa_currency(currency_name="dollar", currency_name="pesos")` |
| weird things people want to know | `cooking_recipe()` | `cooking_recipe()` |
| do i have any reminders for today | `calendar_query(date="today")` | `calendar_query(date="today")` |

## en-US misses

| utterance | gold | pred |
|---|---|---|

## fr-FR hits

| utterance | gold | pred |
|---|---|---|
| pouvez vous trouver nrj | `play_radio(radio_name="nrj")` | `play_radio(radio_name="nrj")` |
| ajouter à mes rappels pour voir nouveau film aujourd'hui à neuf heure du soir | `calendar_set(event_name="voir nouveau film", date="aujourd'hui", time="neuf heure du soir")` | `calendar_set(event_name="voir nouveau film", date="aujourd'hui", time="neuf heure du soir")` |
| montrez-leur où se trouvent les clés des serrures de l'intérieur au cas où ils devraient quitter votre maison rapidement | `alarm_remove()` | `alarm_remove()` |
| rappelle moi mes alarmes aujourd'hui | `alarm_query(date="aujourd'hui")` | `alarm_query(date="aujourd'hui")` |
| préparer un café | `iot_coffee()` | `iot_coffee()` |

## fr-FR misses

| utterance | gold | pred |
|---|---|---|

## ar-SA hits

| utterance | gold | pred |
|---|---|---|
| اجتماع حقي الخميس | `calendar_query(event_name="اجتماع", date="الخميس")` | `calendar_query(event_name="اجتماع", date="الخميس")` |
| هل إيما ستون عزباء | `qa_factoid(person="إيما ستون")` | `qa_factoid(person="إيما ستون")` |
| الجو بارد في الخارج اليوم | `general_quirky(date="اليوم")` | `general_quirky(date="اليوم")` |
| شغل ما كان هذا حب | `play_music(music_genre="ما كان هذا حب")` | `play_music(music_genre="ما كان هذا حب")` |
| حط تنبيه للإجتماع مع المدير | `calendar_set(event_name="للإجتماع", relation="المدير")` | `calendar_set(event_name="للإجتماع", relation="المدير")` |

## ar-SA misses

| utterance | gold | pred |
|---|---|---|
