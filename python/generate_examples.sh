#!/bin/sh

EXAMPLES="altitudes 4578 akopyan_book_5_3_1 napoleon onestep_1"
for example in ${EXAMPLES}; do
  echo -n "Generating ${example}..."
  python visualise_${example}.py > ../examples/${example}.html
  echo " done."
done
