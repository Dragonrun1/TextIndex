# Layers and other compressions

<link rel="stylesheet" href="textindex.css">

---

_This document is an extract from a copyrighted work by [Matt Gemmell](https://mattgemmell.scot). Please do not republish or otherwise reuse it._

---

Physics dictates that you can’t put the same number of keys on a smaller keyboard, assuming the keys themselves are still the usual size. Key sizes are dictated by the way our fingertips have evolved, so something else has to give. This brings us to the topic of _overloading_{^overloading|+"tap dance"}, which was briefly mentioned in the previous section.

Each key must do double (or triple, or more) duty on smaller boards, providing not just the functionality inscribed upon its keycap, but plenty more besides. The question, then, is how to distinguish between a given key’s many possible functions. As is always the case with keyboards, there are several options available.

The matter of how to organise and distribute functionality using these methods is something we’ll cover in the following section; for now, let’s just explore the tools we have available.

## Layers

The primary means of retaining the same amount of functionality despite having fewer physicals keys is to use layers{^}, which is a concept that’s already familiar to any keyboard user.{^layers>"Shift, concept of"##shiftlayer}

The `Shift`{^"Shift (key)"|+#shiftlayer} key is a layer-toggling{^toggle>layer} key, for example, causing other physical keys to temporarily produce different keystrokes, such as uppercase{^} letters instead of lowercase{^}, symbols instead of numbers, and so on. This can be seen very clearly when using the virtual, on-screen keyboards on smartphones and other touch-screen devices, where shifted keys actually change their appearance to indicate their new functions. {^case|uppercase;lowercase}

{^"Apple platforms"##apple}

Viewed in this way, the `Shift` key is in fact a momentary toggle{^!} (i.e. something which only has effect while held down) into what can be thought of as the “Shift layer”{^#shiftlayer}. The modifier keys used for keyboard shortcuts on your operating system, such as the `Command`{^"⌘ (Command/Super key)" |+#apple ~"command key"} or ⌥{^"* (Alt/Option key)"#altkey |+#apple ~altkey} keys on [Apple platforms]{^#apple}, can also be thought of as a layer-toggling{^toggle>layer} key in the same manner. Smaller keyboards simply make use of additional layers compared to larger ones, and often have dedicated keys used to switch into those additional layers.

There are some popular layer setups you’ll encounter on many mechanical keyboards, but you should feel entirely free to create your own system. A common configuration is to have a layer-switching key in each thumb cluster, which provides access to a total of four layers (the base layer, the layer obtained by holding the left hand’s relevant thumb key, the layer for the right hand’s thumb key, and finally the layer for holding both thumb keys simultaneously).

It’s also common to have a layer devoted to navigational controls, keyboard shortcuts, and perhaps media-control functions, and another layer for symbols and special characters, maybe also with a number pad. Sometimes, the fourth layer is reserved for functions pertaining to the keyboard itself, such as controlling its backlighting. But none of this is sacrosanct. Borrow whichever concepts apply to you or appeal to you, and discard the rest. You can always change your mind later.

## Tap dance

The usual way of pressing a key on a keyboard — once, briefly, and then releasing it — can be called a tap. Several modern firmwares (the on-board software) for mechanical keyboards allow additional ways of interacting with a single key. The extremely popular QMK{^} firmware{^|+QMK;+ZMK} calls this feature [_tap dance_]{^"* (QMK feature)"#td!}, and indeed it was originally contributed by a member of the community using the firmware, rather than the core development team.

Tap dance{^#td} allows assigning different actions to different numbers of quick, successive taps on a given key: a single tap could type the letter C, for example, whereas a double-tap could invoke the Copy function to put data onto the system pasteboard. In fact, tap dance also allows distinguishing between taps and holds, similar to how most keyboards will generate a single letter when a key is tapped, but will rapidly repeat that letter if the key is held instead. With tap dance, the tap and/or hold functions can be anything you like, for any key, and this is also true for double-tap, double-tap and hold, and so on.

There’s some overlap here with the section above, because it’s exceptionally common — indeed, almost ubiquitous — for layer-switching keys to in fact also be tap dance keys; they perform a given action when tapped, but they (temporarily) switch layers instead while held. If this concept is new to you, it probably sounds cumbersome and error-prone, and may be so at first, but rest assured that it quickly becomes quite natural.

The aforementioned firmwares, such as QMK{^}, ZMK{^}, and others, all have configuration settings to tweak which govern what precise duration of press is considered a hold rather than a tap, how to interpret the situation when other keys are pressed during the interval, and so on. With a little bit of fine tuning, a reliable and accurate configuration is readily attainable.

It’s worth noting that there is the matter of safety{^} when using keys with multiple modes of function. Certain keystrokes can be considered destructive{^|safety} in some contexts, such as `Delete` or `Backspace` triggering the “Don’t Save” option in certain dialog boxes, erasing highlighted data, and so on. `Enter` could also be considered risky if it commits to publishing or sending something while the work is still being edited. Since tap dance keys can be a source of mis-keying while a new layout is being learned, it’s worth considering whether the (single-) tap action of a tap dance key should perhaps be reserved for safer functions generally.

If we imagine the contrived example of a key which when tapped would invoke Paste and when held would invoke Copy, it’s easy to see that a moment’s distraction, causing the key to be depressed slightly longer than intended, would be dangerous: the spurious and unwanted invocation of Copy instead of Paste would overwrite the data that was already on the pasteboard, causing annoyance and inconvenience at best, and possibly disaster at worst. The specific example is hopefully unlikely, but the general issue is worth remembering. 

By contrast, the intersection of system keyboard shortcuts and tap dance{^#td[_passim_]/} keys can also be enormously convenient. Consider the case of cursor keys which behave normally when tapped, but which when held will act as if a modifier key had also been pressed; most operating systems use this mechanism to navigate and select text in granularities such as whole words, lines, sentences, and paragraphs. For users with corresponding needs, these configurations can be of significant benefit.

## Chords and Combos

In keyboard-related parlance, a _combo_{^*} is exactly what you’d expect it to be, and is what’s more commonly called a keyboard shortcut: pressing a particular combination of keys simultaneously to trigger an action.

`Control+C` will copy selected text to the pasteboard on Windows, and `Command+Control+Q` will lock the screen of a Mac{^#apple}, iPhone, or iPad. Both of these are combos, and there are thousands of others offered by operating systems and applications alike.

You can readily create these for yourself. An example would be if you had a very small keyboard with only ten keys per row, such that its topmost alpha row only has room for the usual letters Q-P. It’s not uncommon in such a situation to configure the board so that pressing `O+P` together will produce the `Backspace` keystroke, as strange as that may sound at first.

There are [ergonomic concerns]{^ergonomics#ergo|+safety} with combos, but they’re very efficient with regard to physical space since they superimpose functionality upon existing keys even within the same layer, so there’s a balance to be struck. It’s ultimately up to your own judgement.

Now comes the wrinkle: you can approach this from the opposite direction too. In the context of creating a keyboard layout, the term _chord_{^*} most commonly refers to creating a single keystroke which will _trigger an entire combo in one press_. For example, you could create a key (perhaps on a layer) which will trigger the aforementioned Apple-device “lock screen” shortcut, without having to actually press the three constituent keys.

Creating such “chord keys” is commonplace in the world of custom layouts. In particular, users of complex applications for purposes such as video or audio editing, music production, graphic design and image manipulation, 3D modelling and so on, can benefit considerably from creating dedicated layers with keys which trigger the shortcuts unique to their daily workhorse apps.

Indeed, entire dedicated keyboards or even more exotic input devices are available, whose sole purpose is to facilitate more efficient interaction with a particular application. A well-made keyboard layout can offer the majority of such functionality with more customisation, and often at lower cost.

To be clear, then, in the context of keyboard layouts and configurations, we’d say that a _single_ given key is a _chord_{^chord!} if pressing it sends _multiple keystrokes simultaneously_ (such as the example of a key which locks a Mac’s screen), whereas we’d say that a _combination of simultaneously-pressed keys_ which perform a single action is a _combo_{^*!} (such as pressing `O+P` to generate `Backspace`).

You can, of course, combine these concepts as you wish, for example by creating a two-key combo{^} which triggers a four-key chord{^}. This can be helpful in the common situation where an action is only occasionally needed, and thus doesn’t warrant a first-class single key of its own, but whose underlying chord is ergonomically{^#ergo>"concerns regarding"} awkward to press. In this context, a “combo chord” serves as a way to redefine a physically difficult pre-existing keyboard shortcut for more comfortable use.

## Macros

{^safety>"regarding macro content"##macrosafety}

Finally, and perhaps most niche, we come to macros. A macro{^macros|+#macrosafety!} could be seen as a close cousin of a chord: the chord{^} triggers multiple keystrokes simultaneously, whereas the macro triggers multiple keystrokes _in sequence_. In practice, macros tend to be used to quickly type commonly-needed chunks of text, like email addresses or other boilerplate{^"* (standard text)"}.

The degree of use you may have for such things is up to you, but exercise caution{^#macrosafety}: any macros that are part of a keyboard layout are present in the keyboard’s own firmware{^}, and thus will still work when the keyboard is plugged into any other computer or device. Thus, macros should _never_ be used to fill-in sensitive information, such as payment details, passwords, and so on. Use biometrically-authenticated completion methods for these things instead, on your own trusted computers and smart devices only.

With the advent of pervasive system-wide autocompletion, text-expansion, and credentials management, keyboard-resident macros have become an ever more marginal feature{^macros>"relevance of"}, but they remain available should you think of a good use for them.

---

## Index

_N.B. Locators with emphasis are definitions._

{index}
