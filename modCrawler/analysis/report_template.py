template_str = """<html><head><meta http-equiv='Content-Type' content='text/html; charset=utf-8' />
<TITLE>$title</TITLE>
<script type="text/javascript" language="javascript" src="https://securehomes.esat.kuleuven.be/~gacar/jscss/jquery-1.9.1.min.js"></script>
 <link rel="stylesheet" href="https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.4/themes/redmond/jquery-ui.css" />
<script src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.4/jquery-ui.min.js"></script>
    <style type="text/css" title="currentStyle">
        @import "https://securehomes.esat.kuleuven.be/~gacar/jscss/css/demo_page.css";
        @import "https://securehomes.esat.kuleuven.be/~gacar/jscss/css/demo_table.css";
    </style>
    <script type="text/javascript" language="javascript" src="https://securehomes.esat.kuleuven.be/~gacar/jscss/jquery.dataTables.min.js"></script>
    <script type="text/javascript" charset="utf-8">

        \$(document).ready(function() {
        \$('#results').dataTable( {
                "aaSorting": [[ 1, "desc" ]],
                "iDisplayLength": -1,
                "aLengthMenu": [[50, 100, -1], [50, 100, "All"]],
                "sDom": '<l<"centered"f><"floatright"p>>rt'
            } );
         \$('#canvas_fp_urls').dataTable( {
                "aaSorting": [[ 1, "desc" ]],
                "iDisplayLength": -1,
                "aLengthMenu": [[50, 100, -1], [50, 100, "All"]],
                "sDom": '<l<"centered"f><"floatright"p>>rt'
            } );
            \$(function() {
                \$( "#tabs" ).tabs({
                  //event: "mouseover"
                });
              });
        } );
    </script>
<style>
.data-table a{
    text-decoration: none;
    color: 3300ff;
}
.data-table td.break{word-break:break-all;}
.data-table img {max-width: 300px; border: 1px dashed gray;}
.data-table {
    border-collapse: collapse;
    font-family: Arial, sans-serif;
}
.data-table td{
    padding: 10px;
    max-width: 600px;
    word-wrap: break-word;
}

#respawning_lso td, #respawning_lso th{
    padding: 10px;
    max-width: 200px;
    word-wrap: break-word;
}

#respawning_lso td.wide, #respawning_lso th.wide{
    padding: 5px;
    max-width: 400px;
    word-wrap: break-word;
}

.data-table tr{
    border: 1px solid silver;
    display:table-row;
}
img.no-border{
    border: none;
}
.bold-text{
    font-weight: bold;
}
.small-text{
    font-size: 0.8em;
}
</style>
    </head>
<body>
    <div id="tabs">
    <ul>
        <li><a href="#tabs-1">Overview</a></li>
        <li><a href="#tabs-2">Canvas Overview</a></li>
        <li><a href="#tabs-3">Canvas Details</a></li>
        <li><a href="#tabs-4">Flash cookies</a></li>
        <li><a href="#tabs-5">localStorage</a></li>
        <li><a href="#tabs-6">Evercookies</a></li>
        <li><a href="#tabs-7">Histograms</a></li>
        <li><a href="#tabs-8">Canvas URLs</a></li>
    </ul>

    <div id="tabs-1">
    <ul>
        <li>Date $start - $end</li>
        <li>Visits: $completed_visits_cnt (of $visits_cnt) completed successfully</li>
        <li>Canvas fingerprinting: $total_canvas_fp_count</li>
        <li>Cookies: $cookies</li>
        <li>localStorage: $localstorage</li>
        <li>Flash cookies(LSO): $flash_cookie_count</li>
    </ul>
    </div> <!--tabs-1 -->

    <div id="tabs-2">
        <table id ="results" class="data-table">
        <thead><tr><th>Domain</th><th>Total Sites</th><th>Canvas fingerprinting scripts from this domain</th></tr></thead>
        <tbody>
        #for $canvas_script_domain, $canvas_scr_urls in $canvas_scr_domains.iteritems()
        <tr>
            <td><a href="$canvas_script_domain" target="_blank"><b>$canvas_script_domain</b></a><br /> 
            (<a href="http://www.iana.org/whois?q=$canvas_script_domain"  target="_blank" class="small-text">Whois</a>
            , <a href="https://www.google.com/#q=$canvas_script_domain"  target="_blank" class="small-text">Google</a>)
            </td>
            <td class="bold-text">$canvas_domain_counts[$canvas_script_domain]</td>
            <td>
                #for $i in $canvas_scr_urls
                    $canvas_url_counts[$i][0] - <a href="$i" target="_blank">$i</a><br />
                #end for
            </td>
        </tr>
        #end for
        <tr class="total">
            <td>TOTAL </td>
            <td>$total_canvas_fp_count</td>
            <td></td>
        </tr>
        </tbody>
        </table>
    </div> <!--tabs-2 -->

    <div id="tabs-3">
        <TABLE id="canvas-details" class="data-table">
        <thead><tr><th>Script URL</th><th>Total Sites</th><th>Domain</th><th>ToDataURL/FillText Data</th><th>Event type / ID</th></tr></thead>
        #for $canvas_scr_url in $canvas_script_urls
            #for $idx, $event in $enumerate($canvas_events_per_script[$canvas_scr_url[0]])
            <TR>
            #if not $idx
                <TD rowspan=$len($canvas_events_per_script[$canvas_scr_url[0]])>
                    <a href="http://$canvas_scr_url[0]" target="_blank">
                        <b>$canvas_scr_url[0]</b>
                    </a>
                </TD>
                <TD rowspan=$len($canvas_events_per_script[$canvas_scr_url[0]])>
                    $canvas_url_counts[$canvas_scr_url[0]][0]
                </TD>
                <TD rowspan=$len($canvas_events_per_script[$canvas_scr_url[0]])>
                    $get_tld($canvas_scr_url[0])
                </TD>
            #end if
                <TD class="break">
                    #if $event[2] == "ToDataURL"
                        <img src="$event[1]" />
                    #else
                        $event[1]
                    #end if
                </TD>
                <TD><b>$event[0]</b> $event[2]</TD>
            </TR>
            #end for
        #end for
        </TABLE>
    </div> <!--tabs-3 -->
    <div id="tabs-4">
    <p>Only Flash cookies found on multiple sites are listed.</p>
    <table id ="flash_cookies" class="data-table">
        <thead><tr><th># of distinct sites</th><th>LSO Domain</th><th>Key</th><th>Value</th><th>Filename</th></tr></thead>
        <tbody>
        #for $flash_cookie in $xsite_flash_cookies
            <tr><td>$flash_cookie[0]</td><td>$flash_cookie[1]</td><td>$flash_cookie[2]</td><td>$flash_cookie[3]</td></tr>
        #end for
        </tbody>
        </table>

    </div> <!--tabs-4 -->
    <div id="tabs-5">
    <p>Only localStorage items found on multiple sites are listed.</p>
    <table id ="local_storage" class="data-table">
        <thead><tr><th># of distinct sites</th><th>Scope (may be more than one)</th><th>Key</th><th>Value</th></tr></thead>
        <tbody>
        #for $xsite_local_storage in $xsite_local_storages
            <tr><td>$xsite_local_storage[0]</td><td>$xsite_local_storage[1]</td><td>$xsite_local_storage[2]</td><td>$xsite_local_storage[3]</td></tr>
        #end for
        </tbody>
        </table>
    </div> <!--tabs-5 -->
    <div id="tabs-6">
    <table id ="respawning_lso" class="data-table">
        <thead><tr><th>Matched string</th><th>LSO Key</th><th class="wide">Complete LSO content</th><th>Domain (LSO)</th><th>LSO path</th><th class="wide">Mathching orig. profile cookies</th><th class="wide">Respawned cookies (pass 1)</th><th class="wide">Respawned cookies (pass 2)</th></tr></thead>
        <tbody>
        #for $respawned_item in $respawned
            <tr><td><b>$respawned_item[0]</b></td><td>$respawned_item[1]</td><td class="wide">$respawned_item[2]</td><td>$respawned_item[3]</td><td>$respawned_item[4]</td><td class="wide">$respawned_item[5]</td><td class="wide">$respawned_item[6]</td><td class="wide">$respawned_item[7]</td></tr>
        #end for
        </tbody>
        </table>
    </div> <!--tabs-6 -->
    <div id="tabs-7">
        #for $fig in $figs
            <img src="$fig" /><br />
        #end for
    </div> <!--tabs-7 -->
    <div id="tabs-8">
    <table id ="canvas_fp_urls" class="data-table">
        <thead><tr><th>Rank</th><th class="wide">Site URL</th><th>Fingerprinter</th></tr></thead>
        <tbody>
        #for $canvas_fp_domain, $canvas_ranks_and_urls in $canvasfp_ranks_urls.iteritems()
            #for $canvas_fp_ranks_and_url in $canvas_ranks_and_urls
                <tr><td>$canvas_fp_ranks_and_url[0]</td><td class="wide">$canvas_fp_ranks_and_url[1]</td><td>$canvas_fp_domain</td></tr>
            #end for
        #end for
        </tbody>
        </table>
    </div> <!--tabs-8 -->
    </div>
</BODY>
</HTML>"""
