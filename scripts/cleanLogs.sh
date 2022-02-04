#! /bin/bash

cd /var/log
du -hs /var/log
prevSize="`du -hs /var/log | grep -o -E '[0-9MG.]+'`"
prevDenomination=${prevSize: -3: 1}
prevSize=${prevSize%G*}
echo "Foldersize before: ${prevSize}${prevDenomination}B"

rm *.gz
counter=0
while [ $counter -le 10 ]
do   
    rm *.$counter
    ((counter++))
done

cd /var/log/journal/b1a989d4d91a4d4c9243369b8c9a170b
rm *

cd /var/log/apt
rm *.gz

cd /var/log/cups
rm *.gz

cd /var/log/unattended-upgrades
rm *.gz

echo Deleted compressed old logs and journal logs


afterSize="`du -hs /var/log | grep -o -E '[0-9MG.]+'`"
afterSize=${afterSize%G*}
echo "Foldersize after: ${afterSize}B"

prevSizeInt=${prevSize::-1}
afterSizeInt=${afterSize::-1}
prevDenomination=${prevSize: -1}
afterDenomination=${afterSize: -1}

if [[ ${prevDenomination} == ${afterDenomination} ]]; then
    echo $((${prevSizeInt}-${afterSizeInt})) ${prevDenomination}B released!
elif [[ ${prevDenomination} == G ]] && [[ ${afterDenomination} == M ]]; then
    afterSizeIntGB="`bc <<< "scale=2; ${prevSizeInt} - ${afterSizeInt}/1024"`"
    echo $afterSizeIntGB ${prevDenomination}B released!!
else
    echo Did not calculate size released
fi

