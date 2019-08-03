# Olimpíadas Científicas

Estamos ainda realizando a migração. Para nosso roadmap veja os [issues](https://github.com/OlimpiadasCientificas/olimpiadascientificas.github.io/issues).

Se quiser nos auxiliar a migrar o site, veja 
https://github.com/OlimpiadasCientificas/olimpiadascientificas.github.io/blob/master/equipes-brasileiras/interdisciplinar/ijso/index.md e https://github.com/OlimpiadasCientificas/olimpiadascientificas.github.io/blob/master/olimpiadas/astronomia/ioaa/index.md
como páginas de exemplo


Toda página de olimpíada precisa de:
<pre>
---  
layout: olimpiada  
title: IOAA  
link: http://www.ioaa2016.in/
image: ioaa.png
fullname: International Olympiad on Astronomy and Astrophysics
---  
</pre>

Qualquer outra informação, como autor, será ignorada no momento e se está presente foi porque ainda não deletamos.


Toda página de equipe precisa de:
<pre>
---  
layout: equipe  
title: IJSO  
---  
</pre>

no topo.



Rode no terminal  kramdown --html-to-native --line-width 220  -i html -o remove_html_tags,kramdown index.html > index.md && rm index.html  para converter os arquivos rapidamente, porém você ainda terá que editar páginas.
Build with jekyll serve --incremental


Para gerar o menu automaticamente, mude auto-menu: false em \_config para auto-menu: true. Quando false, o menu é copiado do arquivo https://github.com/OlimpiadasCientificas/olimpiadascientificas.github.io/blob/master/_includes/fast-menu.html
