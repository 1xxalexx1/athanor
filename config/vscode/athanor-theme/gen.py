#!/usr/bin/env python3
"""Generate the VS Code themes from palette.toml, using the same role mapping
as nvim/colors/athanor.lua (ANSI slot -> syntax role)."""
import colorsys
import json
import tomllib
from pathlib import Path

HERE = Path(__file__).parent
LIGHT = {"vellum", "orpiment"}


def mix(a, b, t):
    """Blend colour a toward b by t (0..1)."""
    pa = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def luminance(c):
    v = [int(c[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def deepen(c, bg, target, boost=1.6):
    """Darken c in HLS, keeping its hue and raising its saturation, until it reaches
    target contrast on bg. The palette's accents sit near 5:1 on the parchment, and
    darkening alone turns them all the same muddy brown."""
    r, g, b = (int(c[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, light, s = colorsys.rgb_to_hls(r, g, b)
    s = min(1.0, s * boost)
    for step in range(101):
        rgb = colorsys.hls_to_rgb(h, light * (1 - step / 100), s)
        out = "#" + "".join(f"{round(x * 255):02x}" for x in rgb)
        if contrast(out, bg) >= target:
            return out
    return out


SYNTAX_CONTRAST = 8.0
QUIET_CONTRAST = 6.0
PAPER_LIFT = 0.55


def build(name, p):
    bg, fg, dim, border, active = p["bg"], p["fg"], p["dim"], p["border"], p["active"]
    bar, barfg = p["bar"], p["barfg"]
    a = p["ansi"]
    red, green, yellow, blue, magenta, cyan = a[1], a[2], a[3], a[4], a[5], a[6]
    gray, bright_red, bright_green, bright_yellow = a[8], a[9], a[10], a[11]
    # The editor sits on a paler sheet in the light schemes, so the accents can keep
    # their color and still stand out; the panels around it stay parchment.
    paper = mix(bg, "#ffffff", PAPER_LIFT) if name in LIGHT else bg
    if name in LIGHT:
        red, green, yellow, blue, magenta, cyan, bright_yellow = (
            deepen(c, paper, SYNTAX_CONTRAST)
            for c in (red, green, yellow, blue, magenta, cyan, bright_yellow)
        )
        gray = deepen(gray, paper, QUIET_CONTRAST)

    raised = mix(bg, fg, 0.06)
    sel = mix(bg, fg, 0.20)
    hover = mix(bg, fg, 0.10)

    ui = {
        "focusBorder": active,
        "foreground": fg,
        "descriptionForeground": dim,
        "disabledForeground": dim,
        "errorForeground": red,
        "icon.foreground": fg,
        "selection.background": mix(bg, yellow, 0.35),
        "widget.border": border,
        "widget.shadow": "#00000030",
        "textLink.foreground": blue,
        "textLink.activeForeground": bright_yellow,
        "textCodeBlock.background": raised,
        "textBlockQuote.border": border,
        "textPreformat.foreground": green,
        "scrollbar.shadow": "#00000000",
        "scrollbarSlider.background": fg + "22",
        "scrollbarSlider.hoverBackground": fg + "40",
        "scrollbarSlider.activeBackground": fg + "55",
        "progressBar.background": yellow,
        "badge.background": active,
        "badge.foreground": bg,
        "button.background": active,
        "button.foreground": bg,
        "button.hoverBackground": mix(active, fg, 0.15),
        "button.secondaryBackground": sel,
        "button.secondaryForeground": fg,
        "dropdown.background": raised,
        "dropdown.border": border,
        "dropdown.foreground": fg,
        "input.background": raised,
        "input.border": border,
        "input.foreground": fg,
        "input.placeholderForeground": dim,
        "inputOption.activeBorder": yellow,
        "inputOption.activeBackground": sel,
        "inputValidation.errorBorder": red,
        "inputValidation.errorBackground": raised,
        "inputValidation.warningBorder": yellow,
        "inputValidation.warningBackground": raised,
        "inputValidation.infoBorder": blue,
        "inputValidation.infoBackground": raised,
        "checkbox.background": raised,
        "checkbox.border": border,
        "list.activeSelectionBackground": sel,
        "list.activeSelectionForeground": fg,
        "list.inactiveSelectionBackground": hover,
        "list.inactiveSelectionForeground": fg,
        "list.hoverBackground": raised,
        "list.focusBackground": sel,
        "list.focusOutline": "#00000000",
        "list.highlightForeground": yellow,
        "list.errorForeground": red,
        "list.warningForeground": yellow,
        "tree.indentGuidesStroke": border,
        "activityBar.background": bg,
        "activityBar.foreground": yellow,
        "activityBar.inactiveForeground": dim,
        "activityBar.border": border,
        "activityBar.activeBorder": yellow,
        "activityBarBadge.background": active,
        "activityBarBadge.foreground": bg,
        "sideBar.background": bg,
        "sideBar.foreground": fg,
        "sideBar.border": border,
        "sideBarTitle.foreground": yellow,
        "sideBarSectionHeader.background": bg,
        "sideBarSectionHeader.foreground": yellow,
        "sideBarSectionHeader.border": border,
        "titleBar.activeBackground": bar,
        "titleBar.activeForeground": barfg,
        "titleBar.inactiveBackground": bar,
        "titleBar.inactiveForeground": mix(bar, barfg, 0.55),
        "titleBar.border": border,
        "menubar.selectionBackground": mix(bar, barfg, 0.15),
        "menubar.selectionForeground": barfg,
        "menu.background": raised,
        "menu.foreground": fg,
        "menu.selectionBackground": sel,
        "menu.selectionForeground": fg,
        "menu.separatorBackground": border,
        "menu.border": border,
        "statusBar.background": bar,
        "statusBar.foreground": barfg,
        "statusBar.border": border,
        "statusBar.noFolderBackground": bar,
        "statusBar.debuggingBackground": active,
        "statusBar.debuggingForeground": bg,
        "statusBarItem.hoverBackground": mix(bar, barfg, 0.15),
        "statusBarItem.remoteBackground": active,
        "statusBarItem.remoteForeground": bg,
        "statusBarItem.errorBackground": p["bar_warn"],
        "statusBarItem.errorForeground": bar,
        "statusBarItem.warningBackground": yellow,
        "statusBarItem.warningForeground": bg,
        "editorGroup.border": border,
        "editorGroupHeader.tabsBackground": bg,
        "editorGroupHeader.tabsBorder": border,
        "editorGroupHeader.noTabsBackground": paper,
        "tab.activeBackground": paper,
        "tab.activeForeground": yellow,
        "tab.activeBorder": yellow,
        "tab.inactiveBackground": bg,
        "tab.inactiveForeground": dim,
        "tab.hoverBackground": raised,
        "tab.hoverForeground": fg,
        "tab.border": border,
        "tab.unfocusedActiveForeground": dim,
        "tab.unfocusedActiveBorder": dim,
        "tab.unfocusedInactiveForeground": dim,
        "breadcrumb.foreground": dim,
        "breadcrumb.focusForeground": yellow,
        "breadcrumb.activeSelectionForeground": yellow,
        "breadcrumbPicker.background": raised,
        "panel.background": bg,
        "panel.border": border,
        "panelTitle.activeForeground": yellow,
        "panelTitle.activeBorder": yellow,
        "panelTitle.inactiveForeground": dim,
        "panelSectionHeader.background": bg,
        "notifications.background": raised,
        "notifications.foreground": fg,
        "notifications.border": border,
        "notificationCenterHeader.background": raised,
        "notificationLink.foreground": blue,
        "notificationsErrorIcon.foreground": red,
        "notificationsWarningIcon.foreground": yellow,
        "notificationsInfoIcon.foreground": blue,
        "quickInput.background": raised,
        "quickInput.foreground": fg,
        "quickInputList.focusBackground": sel,
        "quickInputList.focusForeground": fg,
        "quickInputTitle.background": raised,
        "pickerGroup.foreground": yellow,
        "pickerGroup.border": border,
        "keybindingLabel.background": raised,
        "keybindingLabel.foreground": fg,
        "keybindingLabel.border": border,
        "keybindingLabel.bottomBorder": border,
        "editor.background": paper,
        "editor.foreground": fg,
        "editorCursor.foreground": fg,
        "editor.selectionBackground": sel,
        "editor.inactiveSelectionBackground": hover,
        "editor.selectionHighlightBackground": mix(bg, fg, 0.12),
        "editor.wordHighlightBackground": mix(bg, fg, 0.12),
        "editor.wordHighlightStrongBackground": mix(bg, fg, 0.18),
        "editor.findMatchBackground": mix(bg, yellow, 0.45),
        "editor.findMatchHighlightBackground": mix(bg, yellow, 0.25),
        "editor.findRangeHighlightBackground": mix(bg, fg, 0.08),
        "editor.lineHighlightBackground": mix(bg, fg, 0.05),
        "editor.lineHighlightBorder": "#00000000",
        "editor.hoverHighlightBackground": mix(bg, fg, 0.10),
        "editor.rangeHighlightBackground": mix(bg, fg, 0.08),
        "editor.foldBackground": mix(bg, fg, 0.06),
        "editorLineNumber.foreground": gray,
        "editorLineNumber.activeForeground": yellow,
        "editorIndentGuide.background1": border,
        "editorIndentGuide.activeBackground1": gray,
        "editorWhitespace.foreground": border,
        "editorRuler.foreground": border,
        "editorCodeLens.foreground": dim,
        "editorInlayHint.foreground": dim,
        "editorInlayHint.background": "#00000000",
        "editorLink.activeForeground": blue,
        "editorBracketMatch.background": "#00000000",
        "editorBracketMatch.border": yellow,
        "editorBracketHighlight.foreground1": red,
        "editorBracketHighlight.foreground2": yellow,
        "editorBracketHighlight.foreground3": blue,
        "editorBracketHighlight.foreground4": green,
        "editorBracketHighlight.foreground5": magenta,
        "editorBracketHighlight.foreground6": cyan,
        "editorBracketHighlight.unexpectedBracket.foreground": red,
        "editorError.foreground": red,
        "editorWarning.foreground": yellow,
        "editorInfo.foreground": blue,
        "editorHint.foreground": dim,
        "editorGutter.background": paper,
        "editorGutter.addedBackground": green,
        "editorGutter.modifiedBackground": yellow,
        "editorGutter.deletedBackground": red,
        "editorOverviewRuler.border": "#00000000",
        "editorOverviewRuler.errorForeground": red,
        "editorOverviewRuler.warningForeground": yellow,
        "editorOverviewRuler.infoForeground": blue,
        "editorOverviewRuler.addedForeground": green,
        "editorOverviewRuler.modifiedForeground": yellow,
        "editorOverviewRuler.deletedForeground": red,
        "editorOverviewRuler.findMatchForeground": yellow,
        "editorOverviewRuler.selectionHighlightForeground": gray,
        "editorWidget.background": raised,
        "editorWidget.foreground": fg,
        "editorWidget.border": border,
        "editorSuggestWidget.background": raised,
        "editorSuggestWidget.border": border,
        "editorSuggestWidget.foreground": fg,
        "editorSuggestWidget.selectedBackground": sel,
        "editorSuggestWidget.highlightForeground": yellow,
        "editorHoverWidget.background": raised,
        "editorHoverWidget.border": border,
        "peekView.border": border,
        "peekViewEditor.background": raised,
        "peekViewResult.background": raised,
        "peekViewTitle.background": raised,
        "peekViewTitleLabel.foreground": yellow,
        "peekViewResult.selectionBackground": sel,
        "peekViewEditor.matchHighlightBackground": mix(bg, yellow, 0.35),
        "diffEditor.insertedTextBackground": green + "26",
        "diffEditor.removedTextBackground": red + "26",
        "diffEditor.insertedLineBackground": green + "14",
        "diffEditor.removedLineBackground": red + "14",
        "gitDecoration.addedResourceForeground": green,
        "gitDecoration.modifiedResourceForeground": yellow,
        "gitDecoration.deletedResourceForeground": red,
        "gitDecoration.untrackedResourceForeground": bright_green,
        "gitDecoration.ignoredResourceForeground": dim,
        "gitDecoration.conflictingResourceForeground": bright_red,
        "gitDecoration.stageModifiedResourceForeground": yellow,
        "gitDecoration.stageDeletedResourceForeground": red,
        "gitDecoration.submoduleResourceForeground": blue,
        "minimap.background": paper,
        "minimap.selectionHighlight": yellow,
        "minimap.findMatchHighlight": yellow,
        "minimap.errorHighlight": red,
        "minimap.warningHighlight": yellow,
        "minimapGutter.addedBackground": green,
        "minimapGutter.modifiedBackground": yellow,
        "minimapGutter.deletedBackground": red,
        "terminal.background": bg,
        "terminal.foreground": fg,
        "terminal.selectionBackground": sel,
        "terminalCursor.foreground": fg,
        "terminal.border": border,
        "debugToolBar.background": raised,
        "debugIcon.breakpointForeground": red,
        "testing.iconPassed": green,
        "testing.iconFailed": red,
        "testing.iconErrored": red,
        "settings.headerForeground": yellow,
        "settings.modifiedItemIndicator": yellow,
        "charts.red": red,
        "charts.yellow": yellow,
        "charts.blue": blue,
        "charts.green": green,
        "charts.purple": magenta,
        "charts.orange": bright_red,
    }
    names = ["Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White"]
    for i, n in enumerate(names):
        ui[f"terminal.ansi{n}"] = a[i]
        ui[f"terminal.ansiBright{n}"] = a[i + 8]

    def rule(scope, color=None, style=None):
        s = {}
        if color:
            s["foreground"] = color
        if style is not None:
            s["fontStyle"] = style
        return {"scope": scope, "settings": s}

    tokens = [
        rule(["comment", "punctuation.definition.comment"], gray, ""),
        rule(["string", "punctuation.definition.string", "string.quoted"], green),
        rule(["constant.character.escape", "string.regexp", "constant.other.character-class.regexp"], cyan),
        rule(["constant", "constant.numeric", "constant.language", "support.constant", "variable.other.enummember", "variable.other.constant"], magenta),
        rule(["keyword", "keyword.control", "storage", "storage.type", "storage.modifier", "keyword.other"], red),
        rule(["keyword.operator", "punctuation", "meta.brace", "punctuation.separator", "punctuation.terminator"], gray),
        rule(["keyword.operator.new", "keyword.operator.expression", "keyword.operator.word", "keyword.operator.logical.python", "keyword.operator.wordlike"], red),
        rule(["entity.name.function", "support.function", "meta.function-call entity.name.function", "variable.function"], bright_yellow),
        rule(["entity.name.function.macro", "support.function.macro", "entity.name.function.preprocessor", "meta.preprocessor"], yellow),
        rule(["entity.name.type", "entity.name.class", "entity.name.struct", "entity.name.enum", "entity.name.interface", "entity.other.inherited-class", "support.type", "support.class", "entity.name.type.parameter"], cyan),
        rule(["storage.type.primitive", "storage.type.built-in", "support.type.primitive", "keyword.type"], cyan),
        rule(["support.type.property-name", "meta.object-literal.key", "variable.other.property", "variable.other.object.property", "variable.parameter"], fg),
        rule(["variable.language", "variable.other.predefined"], yellow),
        rule(["entity.name.namespace", "entity.name.module", "support.module", "entity.name.package"], blue),
        rule(["meta.decorator", "meta.attribute", "storage.type.annotation", "entity.name.function.decorator", "punctuation.definition.annotation"], blue),
        rule(["entity.name.tag", "punctuation.definition.tag.begin", "punctuation.definition.tag.end"], red),
        rule(["entity.other.attribute-name"], blue),
        rule(["entity.name.label"], yellow),
        # Markdown: every element gets its own hue, not just a font style.
        rule(["markup.heading", "entity.name.section", "punctuation.definition.heading"], red, "bold"),
        rule(["markup.bold", "punctuation.definition.bold"], bright_yellow, "bold"),
        rule(["markup.italic", "punctuation.definition.italic"], magenta, "italic"),
        rule(["markup.bold markup.italic", "markup.italic markup.bold"], magenta, "bold italic"),
        rule(["markup.strikethrough"], gray, "strikethrough"),
        rule(["string.other.link", "meta.link.reference.def entity.name"], blue),
        rule(["markup.underline.link"], cyan, "underline"),
        rule(["markup.inline.raw", "markup.fenced_code", "markup.raw"], green),
        rule(["markup.quote"], gray, "italic"),
        rule(["punctuation.definition.list.begin", "beginning.punctuation.definition.list"], cyan),
        rule(["meta.separator"], gray),
        rule(["markup.inserted", "meta.diff.header.to-file"], green),
        rule(["markup.deleted", "meta.diff.header.from-file"], red),
        rule(["markup.changed"], yellow),
        rule(["invalid", "invalid.illegal"], red, "bold"),
        rule(["invalid.deprecated"], None, "strikethrough"),
    ]

    semantic = {
        "namespace": blue,
        "class": cyan,
        "struct": cyan,
        "enum": cyan,
        "interface": cyan,
        "type": cyan,
        "typeParameter": cyan,
        "function": bright_yellow,
        "method": bright_yellow,
        "macro": yellow,
        "decorator": blue,
        "enumMember": magenta,
        "variable": fg,
        "parameter": fg,
        "property": fg,
        "keyword": red,
        "comment": gray,
        "string": green,
        "number": magenta,
        "operator": gray,
    }

    return {
        "name": f"Athanor {p['label']}",
        "type": "light" if name in LIGHT else "dark",
        "semanticHighlighting": True,
        "colors": ui,
        "tokenColors": tokens,
        "semanticTokenColors": semantic,
    }


def main():
    palette = tomllib.loads((HERE / "palette.toml").read_text())
    for name, p in palette.items():
        theme = build(name, p)
        out = HERE / "themes" / f"athanor-{name}-color-theme.json"
        out.write_text(json.dumps(theme, indent=2) + "\n")
        print(out.name, len(theme["colors"]), "colors")


if __name__ == "__main__":
    main()
