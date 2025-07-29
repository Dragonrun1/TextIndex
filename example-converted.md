# Layers and other compressions

<link rel="stylesheet" href="textindex.css">

---

_This document is an extract from a copyrighted work by [Matt Gemmell](https://mattgemmell.scot). Please do not republish or otherwise reuse it._

---

Physics dictates that you can’t put the same number of keys on a smaller keyboard, assuming the keys themselves are still the usual size. Key sizes are dictated by the way our fingertips have evolved, so something else has to give. This brings us to the topic of <span id="idx1" class="textindex"><em>overloading</em></span>, which was briefly mentioned in the previous section.

Each key must do double (or triple, or more) duty on smaller boards, providing not just the functionality inscribed upon its keycap, but plenty more besides. The question, then, is how to distinguish between a given key’s many possible functions. As is always the case with keyboards, there are several options available.

The matter of how to organise and distribute functionality using these methods is something we’ll cover in the following section; for now, let’s just explore the tools we have available.

## Layers

The primary means of retaining the same amount of functionality despite having fewer physicals keys is to use <span id="idx2" class="textindex">layers</span>, which is a concept that’s already familiar to any keyboard user.

The <span id="idx3" class="textindex">`Shift`</span> key is a <span id="idx4" class="textindex">layer-toggling</span> key, for example, causing other physical keys to temporarily produce different keystrokes, such as <span id="idx5" class="textindex">uppercase</span> letters instead of <span id="idx6" class="textindex">lowercase</span>, symbols instead of numbers, and so on. This can be seen very clearly when using the virtual, on-screen keyboards on smartphones and other touch-screen devices, where shifted keys actually change their appearance to indicate their new functions. <span id="idx7" class="textindex"></span>



Viewed in this way, the `Shift` key is in fact a momentary <span id="idx8" class="textindex">toggle</span> (i.e. something which only has effect while held down) into what can be thought of as the “Shift <span id="idx9" class="textindex">layer”</span>. The modifier keys used for keyboard shortcuts on your operating system, such as the <span id="idx10" class="textindex">`Command`</span> or <span id="idx11" class="textindex">⌥</span> keys on <span id="idx12" class="textindex">Apple platforms</span>, can also be thought of as a <span id="idx13" class="textindex">layer-toggling</span> key in the same manner. Smaller keyboards simply make use of additional layers compared to larger ones, and often have dedicated keys used to switch into those additional layers.

There are some popular layer setups you’ll encounter on many mechanical keyboards, but you should feel entirely free to create your own system. A common configuration is to have a layer-switching key in each thumb cluster, which provides access to a total of four layers (the base layer, the layer obtained by holding the left hand’s relevant thumb key, the layer for the right hand’s thumb key, and finally the layer for holding both thumb keys simultaneously).

It’s also common to have a layer devoted to navigational controls, keyboard shortcuts, and perhaps media-control functions, and another layer for symbols and special characters, maybe also with a number pad. Sometimes, the fourth layer is reserved for functions pertaining to the keyboard itself, such as controlling its backlighting. But none of this is sacrosanct. Borrow whichever concepts apply to you or appeal to you, and discard the rest. You can always change your mind later.

## Tap dance

The usual way of pressing a key on a keyboard — once, briefly, and then releasing it — can be called a tap. Several modern firmwares (the on-board software) for mechanical keyboards allow additional ways of interacting with a single key. The extremely popular <span id="idx14" class="textindex">QMK</span> <span id="idx15" class="textindex">firmware</span> calls this feature <span id="idx16" class="textindex"><em>tap dance</em></span>, and indeed it was originally contributed by a member of the community using the firmware, rather than the core development team.

Tap <span id="idx17" class="textindex">dance</span> allows assigning different actions to different numbers of quick, successive taps on a given key: a single tap could type the letter C, for example, whereas a double-tap could invoke the Copy function to put data onto the system pasteboard. In fact, tap dance also allows distinguishing between taps and holds, similar to how most keyboards will generate a single letter when a key is tapped, but will rapidly repeat that letter if the key is held instead. With tap dance, the tap and/or hold functions can be anything you like, for any key, and this is also true for double-tap, double-tap and hold, and so on.

There’s some overlap here with the section above, because it’s exceptionally common — indeed, almost ubiquitous — for layer-switching keys to in fact also be tap dance keys; they perform a given action when tapped, but they (temporarily) switch layers instead while held. If this concept is new to you, it probably sounds cumbersome and error-prone, and may be so at first, but rest assured that it quickly becomes quite natural.

The aforementioned firmwares, such as <span id="idx18" class="textindex">QMK</span>, <span id="idx19" class="textindex">ZMK</span>, and others, all have configuration settings to tweak which govern what precise duration of press is considered a hold rather than a tap, how to interpret the situation when other keys are pressed during the interval, and so on. With a little bit of fine tuning, a reliable and accurate configuration is readily attainable.

It’s worth noting that there is the matter of <span id="idx20" class="textindex">safety</span> when using keys with multiple modes of function. Certain keystrokes can be considered <span id="idx21" class="textindex">destructive</span> in some contexts, such as `Delete` or `Backspace` triggering the “Don’t Save” option in certain dialog boxes, erasing highlighted data, and so on. `Enter` could also be considered risky if it commits to publishing or sending something while the work is still being edited. Since tap dance keys can be a source of mis-keying while a new layout is being learned, it’s worth considering whether the (single-) tap action of a tap dance key should perhaps be reserved for safer functions generally.

If we imagine the contrived example of a key which when tapped would invoke Paste and when held would invoke Copy, it’s easy to see that a moment’s distraction, causing the key to be depressed slightly longer than intended, would be dangerous: the spurious and unwanted invocation of Copy instead of Paste would overwrite the data that was already on the pasteboard, causing annoyance and inconvenience at best, and possibly disaster at worst. The specific example is hopefully unlikely, but the general issue is worth remembering. 

By contrast, the intersection of system keyboard shortcuts and tap <span id="idx22" class="textindex">dance</span> keys can also be enormously convenient. Consider the case of cursor keys which behave normally when tapped, but which when held will act as if a modifier key had also been pressed; most operating systems use this mechanism to navigate and select text in granularities such as whole words, lines, sentences, and paragraphs. For users with corresponding needs, these configurations can be of significant benefit.

## Chords and Combos

In keyboard-related parlance, a <span id="idx23" class="textindex"><em>combo</em></span> is exactly what you’d expect it to be, and is what’s more commonly called a keyboard shortcut: pressing a particular combination of keys simultaneously to trigger an action.

`Control+C` will copy selected text to the pasteboard on Windows, and `Command+Control+Q` will lock the screen of a <span id="idx24" class="textindex">Mac</span>, iPhone, or iPad. Both of these are combos, and there are thousands of others offered by operating systems and applications alike.

You can readily create these for yourself. An example would be if you had a very small keyboard with only ten keys per row, such that its topmost alpha row only has room for the usual letters Q-P. It’s not uncommon in such a situation to configure the board so that pressing `O+P` together will produce the `Backspace` keystroke, as strange as that may sound at first.

There are <span id="idx25" class="textindex">ergonomic concerns</span> with combos, but they’re very efficient with regard to physical space since they superimpose functionality upon existing keys even within the same layer, so there’s a balance to be struck. It’s ultimately up to your own judgement.

Now comes the wrinkle: you can approach this from the opposite direction too. In the context of creating a keyboard layout, the term <span id="idx26" class="textindex"><em>chord</em></span> most commonly refers to creating a single keystroke which will _trigger an entire combo in one press_. For example, you could create a key (perhaps on a layer) which will trigger the aforementioned Apple-device “lock screen” shortcut, without having to actually press the three constituent keys.

Creating such “chord keys” is commonplace in the world of custom layouts. In particular, users of complex applications for purposes such as video or audio editing, music production, graphic design and image manipulation, 3D modelling and so on, can benefit considerably from creating dedicated layers with keys which trigger the shortcuts unique to their daily workhorse apps.

Indeed, entire dedicated keyboards or even more exotic input devices are available, whose sole purpose is to facilitate more efficient interaction with a particular application. A well-made keyboard layout can offer the majority of such functionality with more customisation, and often at lower cost.

To be clear, then, in the context of keyboard layouts and configurations, we’d say that a _single_ given key is a <span id="idx27" class="textindex"><em>chord</em></span> if pressing it sends _multiple keystrokes simultaneously_ (such as the example of a key which locks a Mac’s screen), whereas we’d say that a _combination of simultaneously-pressed keys_ which perform a single action is a <span id="idx28" class="textindex"><em>combo</em></span> (such as pressing `O+P` to generate `Backspace`).

You can, of course, combine these concepts as you wish, for example by creating a two-key <span id="idx29" class="textindex">combo</span> which triggers a four-key <span id="idx30" class="textindex">chord</span>. This can be helpful in the common situation where an action is only occasionally needed, and thus doesn’t warrant a first-class single key of its own, but whose underlying chord is <span id="idx31" class="textindex">ergonomically</span> awkward to press. In this context, a “combo chord” serves as a way to redefine a physically difficult pre-existing keyboard shortcut for more comfortable use.

## Macros


Finally, and perhaps most niche, we come to macros. A <span id="idx32" class="textindex">macro</span> could be seen as a close cousin of a chord: the <span id="idx33" class="textindex">chord</span> triggers multiple keystrokes simultaneously, whereas the macro triggers multiple keystrokes _in sequence_. In practice, macros tend to be used to quickly type commonly-needed chunks of text, like email addresses or other <span id="idx34" class="textindex">boilerplate</span>.

The degree of use you may have for such things is up to you, but exercise <span id="idx35" class="textindex">caution</span>: any macros that are part of a keyboard layout are present in the keyboard’s own <span id="idx36" class="textindex">firmware</span>, and thus will still work when the keyboard is plugged into any other computer or device. Thus, macros should _never_ be used to fill-in sensitive information, such as payment details, passwords, and so on. Use biometrically-authenticated completion methods for these things instead, on your own trusted computers and smart devices only.

With the advent of pervasive system-wide autocompletion, text-expansion, and credentials management, keyboard-resident macros have become an ever more marginal <span id="idx37" class="textindex">feature</span>, but they remain available should you think of a good use for them.

---

## Index

_N.B. Locators with emphasis are definitions._

<dl class="textindex index">
	<dt><span class="entry-heading">⌥ (Alt/Option key)</span><span class="entry-references">, <a class="locator" href="#idx11" data-index-id="11" data-index-id-elided="11"></a>. <em>See also</em> Apple platforms</span></dt>
	<dt><span class="entry-heading">Apple platforms</span><span class="entry-references">, <a class="locator" href="#idx12" data-index-id="12" data-index-id-elided="12"></a>, <a class="locator" href="#idx24" data-index-id="24" data-index-id-elided="24"></a></span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">boilerplate (standard text)</span><span class="entry-references">, <a class="locator" href="#idx34" data-index-id="34" data-index-id-elided="34"></a></span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">case</span><span class="entry-references">. <em>See</em> lowercase; uppercase</span></dt>
	<dt><span class="entry-heading">chord</span><span class="entry-references">, <a class="locator" href="#idx26" data-index-id="26" data-index-id-elided="26"></a>, <em><a class="locator" href="#idx27" data-index-id="27" data-index-id-elided="27"></a></em>, <a class="locator" href="#idx30" data-index-id="30" data-index-id-elided="30"></a>, <a class="locator" href="#idx33" data-index-id="33" data-index-id-elided="33"></a></span></dt>
	<dt><span class="entry-heading">combo</span><span class="entry-references">, <a class="locator" href="#idx23" data-index-id="23" data-index-id-elided="23"></a>, <em><a class="locator" href="#idx28" data-index-id="28" data-index-id-elided="28"></a></em>, <a class="locator" href="#idx29" data-index-id="29" data-index-id-elided="29"></a></span></dt>
	<dt><span class="entry-heading">⌘ (Command/Super key)</span><span class="entry-references">, <a class="locator" href="#idx10" data-index-id="10" data-index-id-elided="10"></a>. <em>See also</em> Apple platforms</span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">destructive</span><span class="entry-references">. <em>See</em> safety</span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">ergonomics</span><span class="entry-references">, <a class="locator" href="#idx25" data-index-id="25" data-index-id-elided="25"></a></span></dt>
	<dd>
		<dl>
			<dt><span class="entry-heading">concerns regarding</span><span class="entry-references">, <a class="locator" href="#idx31" data-index-id="31" data-index-id-elided="31"></a></span></dt>
			<dt><span class="entry-references"><em>See also</em> safety</span></dt>
		</dl>
	</dd>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">firmware</span><span class="entry-references">, <a class="locator" href="#idx15" data-index-id="15" data-index-id-elided="15"></a>, <a class="locator" href="#idx36" data-index-id="36" data-index-id-elided="36"></a>. <em>See also</em> QMK; ZMK</span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">layers</span><span class="entry-references">, <a class="locator" href="#idx2" data-index-id="2" data-index-id-elided="2"></a></span></dt>
	<dd>
		<dl>
			<dt><span class="entry-heading">Shift, concept of</span><span class="entry-references">, <a class="locator" href="#idx9" data-index-id="9" data-index-id-elided="9"></a></span></dt>
		</dl>
	</dd>
	<dt><span class="entry-heading">lowercase</span><span class="entry-references">, <a class="locator" href="#idx6" data-index-id="6" data-index-id-elided="6"></a></span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">macros</span><span class="entry-references">, <em><a class="locator" href="#idx32" data-index-id="32" data-index-id-elided="32"></a></em></span></dt>
	<dd>
		<dl>
			<dt><span class="entry-heading">relevance of</span><span class="entry-references">, <a class="locator" href="#idx37" data-index-id="37" data-index-id-elided="37"></a></span></dt>
			<dt><span class="entry-references"><em>See also</em> safety: regarding macro content</span></dt>
		</dl>
	</dd>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">overloading</span><span class="entry-references">, <a class="locator" href="#idx1" data-index-id="1" data-index-id-elided="1"></a>. <em>See also</em> tap dance</span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">QMK</span><span class="entry-references">, <a class="locator" href="#idx14" data-index-id="14" data-index-id-elided="14"></a>, <a class="locator" href="#idx18" data-index-id="18" data-index-id-elided="18"></a></span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">safety</span><span class="entry-references">, <a class="locator" href="#idx20" data-index-id="20" data-index-id-elided="20"></a></span></dt>
	<dd>
		<dl>
			<dt><span class="entry-heading">regarding macro content</span><span class="entry-references">, <a class="locator" href="#idx35" data-index-id="35" data-index-id-elided="35"></a></span></dt>
		</dl>
	</dd>
	<dt><span class="entry-heading">Shift (key)</span><span class="entry-references">, <a class="locator" href="#idx3" data-index-id="3" data-index-id-elided="3"></a>. <em>See also</em> layers: Shift, concept of</span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">tap dance (QMK feature)</span><span class="entry-references">, <em><a class="locator" href="#idx16" data-index-id="16" data-index-id-elided="16"></a></em>, <a class="locator" href="#idx17" data-index-id="17" data-index-id-elided="17"></a>–<a class="locator" href="#idx22" data-index-id="22" data-index-id-elided="22"></a> _passim_</span></dt>
	<dt><span class="entry-heading">toggle</span><span class="entry-references">, <em><a class="locator" href="#idx8" data-index-id="8" data-index-id-elided="8"></a></em></span></dt>
	<dd>
		<dl>
			<dt><span class="entry-heading">layer</span><span class="entry-references">, <a class="locator" href="#idx4" data-index-id="4" data-index-id-elided="4"></a>, <a class="locator" href="#idx13" data-index-id="13" data-index-id-elided="13"></a></span></dt>
		</dl>
	</dd>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">uppercase</span><span class="entry-references">, <a class="locator" href="#idx5" data-index-id="5" data-index-id-elided="5"></a></span></dt>
	<dt class="group-separator">&nbsp;</dt>
	<dt><span class="entry-heading">ZMK</span><span class="entry-references">, <a class="locator" href="#idx19" data-index-id="19" data-index-id-elided="19"></a></span></dt>
</dl>
