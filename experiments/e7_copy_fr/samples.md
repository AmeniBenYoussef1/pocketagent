# Samples

## fr-FR hits

| utterance | gold | pred |
|---|---|---|
| tamiser les lumières dans la salle | `iot_hue_lightdim(house_place="salle")` | `iot_hue_lightdim(house_place="salle")` |
| donne-moi l'état de ma mémoire disponible | `general_quirky()` | `general_quirky()` |
| liste les options de livraison les plus notées pour la nourriture chinois | `takeaway_query(order_type="livraison", food_type="chinois")` | `takeaway_query(order_type="livraison", food_type="chinois")` |
| j'aimerais écouter ne me quitte pas de jacques brel | `play_music(song_name="ne me quitte pas", artist_name="jacques brel")` | `play_music(song_name="ne me quitte pas", artist_name="jacques brel")` |
| joue ne me quitte pas | `play_music(song_name="ne me quitte pas")` | `play_music(song_name="ne me quitte pas")` |

## fr-FR misses

| utterance | gold | pred |
|---|---|---|
| éteigne les lumières s'il te plait | `iot_hue_lightoff()` | `iot_hue_lightdim()` |
| rendre une chambre foncée | `iot_hue_lightdim(house_place="chambre")` | `iot_hue_lightchange(house_place="chambre foncée")` |
| nettoyer la télévision | `iot_cleaning(house_place="télévision")` | `iot_cleaning(device_type="télévision")` |
| le nettoyage est bon la poussière est si mauvaise fais maintenant ta magie nettoie mon tapis | `iot_cleaning(house_place="tapis")` | `general_quirky()` |
| trouve mes plats à emporter thaïlandais autour de la concorde | `takeaway_query(order_type="plats à emporter", food_type="thaïlandais", place_name="la concorde")` | `takeaway_query(order_type="plats à emporter", place_name="thaïlandais", place_name="la concorde")` |
| jouer moi jacques brel ne me quitte pas | `play_music()` | `play_music(artist_name="jacques brel", song_name="ne me quitte pas")` |
| quel est le groupe qui chante maintenant | `music_query()` | `music_query(event_name="groupe")` |
| qu'est-ce qu'il y a avec ma commande de dîner | `takeaway_query()` | `takeaway_query(food_type="dîner")` |
| quelles sont les prévisions de cette semaine | `weather_query(time="de cette semaine")` | `weather_query(date="de cette semaine")` |
| boucle cette piste | `music_settings(player_setting="boucle")` | `music_dislikeness()` |
