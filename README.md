A utility to provide additional information about which lines
correspond in the two files being compared.

On some files with many or large changes diff utilities sometimes fail
to "line up" the two files correctly creating spurious and confusing diffs.

For example if you know line 100 in foo.txt and line 200 in bar.txt
are the same a standard diff utility may produce differences that do
not show line 100 being a modification of line 200. Similarly nearby
lines are not correctly matched.

On the other hand, diffalign.py allows you to say that these two
points are the same creating more meaningful diffs.
