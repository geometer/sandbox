#!/bin/sh

for example in altitudes 4578 akopyan_book_4_1_1 akopyan_book_5_3_1 napoleon onestep_1; do
  echo -n "Generating ${example}..."
  python visualise_${example}.py > ../examples/${example}.html
  echo " done."
done
