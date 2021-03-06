sandbox$ = {

selectedObjects: {},
board: null,
index_usages: [0, 0, 0, 0, 0],

options: {
	color: '#212121',
	hl_colors: ['#F4433680', '#4CAF5080', '#FF980080', '#2196F380', '#00968880']
},

createScene: function(json) {
	var scene = JSON.parse(json);
	var xs = [];
	var ys = [];
	scene.points.forEach(pt => {
		xs.push(pt.x);
		ys.push(pt.y);
	});
	scene.circles.forEach(circ => {
		xs.push(circ.x + circ.radius);
		xs.push(circ.x - circ.radius);
		ys.push(circ.y + circ.radius);
		ys.push(circ.y - circ.radius);
	});
	var max_x = Math.max(... xs);
	var min_x = Math.min(... xs);
	var max_y = Math.max(... ys);
	var min_y = Math.min(... ys);
  var mid_x = (min_x + max_x) / 2;
  var mid_y = (min_y + max_y) / 2;
	var size = Math.max(max_x - min_x, max_y - min_y) * 1.3;
	this.board = JXG.JSXGraph.initBoard('sandbox-scene', {
		boundingbox: [mid_x - size / 2, mid_y - size / 2, mid_x + size / 2, mid_y + size / 2],
		keepaspectratio: true,
		showNavigation: false,
		showCopyright: false,
		registerEvents: false
	});

	scene.points.forEach(pt => {
		this.board.create('point', [pt.x, pt.y], {
			name: pt.name,
			id: pt.name,
			color: this.options.color,
			size: 3,
			label: {color: this.options.color, autoPosition: true}
		});
	});

	scene.lines.forEach(line => {
		this.board.create('line', [line.pt0, line.pt1], {
			straightFirst: false,
			straightLast: false,
			strokeWidth: 0.7,
			color: this.options.color
		});
	});

	scene.circles.forEach(circle => {
		this.board.create('circle', [[circle.x, circle.y], circle.radius], {
			fillOpacity: 0,
			strokeWidth: 0.7,
			color: this.options.color
		});
	});

	setTimeout(function() {
		console.debug('labels layout hack');
		sandbox$.board.update();
	}, 0);
},

beautifiedLine: function(line) {
	var vert = '<span style=\'font-size:130%;vertical-align:-2px;\'>|</span>';
	return line.replace(/\|([^|]*)\|/g, '<span style=\'white-space:nowrap\'>' + vert + '$1' + vert + '</span>');
},

createFigureReferences: function() {
	var desc = $('#sandbox-description');

	$('.sandbox-text').find('.figure').each(function() {
		var clazz = null;
		var points = null;
		var lines = [];
		$(this)[0].classList.forEach(cls => {
			clazz = cls;
			if (cls.startsWith('tr__')) {
				points = cls.split('__').slice(1);
				lines = [
					{s: points[0], e: points[1]},
					{s: points[0], e: points[2]},
					{s: points[1], e: points[2]}
				];
			} else if (cls.startsWith('plg__')) {
				points = cls.split('__').slice(1);
				for (var i = 0; i < points.length; ++i) {
					lines.push({s: points[i], e: points[(i + 1) % points.length]});
				}
			} else if (cls.startsWith('ang__')) {
				points = cls.split('__').slice(1);
				lines = [
					{s: points[1], e: points[0], type: 'ray'},
					{s: points[1], e: points[2], type: 'ray'}
				];
			} else if (cls.startsWith('ang4__')) {
				points = cls.split('__').slice(1);
				lines = [
					{s: points[0], e: points[1], type: 'ray'},
					{s: points[2], e: points[3], type: 'ray'}
				];
			} else if (cls.startsWith('vec__')) {
				points = cls.split('__').slice(1);
				lines = [{s: points[0], e: points[1]}];
			} else if (cls.startsWith('ray__')) {
				points = cls.split('__').slice(1);
				lines = [{s: points[0], e: points[1], type: 'ray'}];
			} else if (cls.startsWith('ln__')) {
				points = cls.split('__').slice(1);
				lines = [{s: points[0], e: points[1], type: 'line'}];
			} else if (cls.startsWith('seg__')) {
				points = cls.split('__').slice(1);
				lines = [{s: points[0], e: points[1]}];
			} else if (cls.startsWith('cyc__')) {
				points = cls.split('__').slice(1);
				// TODO: add lines
			} else if (cls.startsWith('pt__')) {
				points = cls.split('__').slice(1);
			}
		});

		if (points) {
			$(this).click(function() {
				var deselect = function() {
					$('#sandbox-selections').find('.' + clazz).each(function() {
						$(this).next().remove();
						$(this).remove();
					});
					var index = sandbox$.selectedObjects[clazz].index;
					sandbox$.index_usages[index] -= 1;
					sandbox$.selectedObjects[clazz].set.forEach(obj => {sandbox$.board.removeObject(obj);});
					delete sandbox$.selectedObjects[clazz];
					desc.find('.' + clazz).each(function() {
						$(this).removeClass('selected');
						$(this).removeClass('selected' + index);
					});
					$('.sandbox-text .' + clazz).each(function() {
						$(this).removeClass('selected');
						$(this).removeClass('selected' + index);
					});
				};
				if ($(this).hasClass('selected')) {
					deselect();
				} else {
					var index = sandbox$.index_usages.indexOf(Math.min(...sandbox$.index_usages));
					var color = sandbox$.options.hl_colors[index];
					sandbox$.index_usages[index] += 1;
					var clone = $(this).clone();
					clone.addClass('selected');
					clone.addClass('selected' + index);
					clone.click(deselect);
					var area = $('#sandbox-selections');
					area.append(clone);
					area.append('<span class="space"/>');
					var selected = [];
					points.forEach(id => {
						selected.push(sandbox$.board.create(
							'point', ['X(' + id + ')', 'Y(' + id + ')'], {
								color: color,
								size: 5,
								withLabel: false
							})
						);
					});
					lines.forEach(ln => {
						selected.push(sandbox$.board.create(
							'line', [ln['s'], ln['e']], {
								straightFirst: ln['type'] == 'line',
								straightLast: ln['type'] == 'ray' || ln['type'] == 'line',
								color: color,
								lineCap: 'round',
								strokeWidth: 7.0
							})
						);
					});
					sandbox$.selectedObjects[clazz] = {'set': selected, 'index': index};
					desc.find('.' + clazz).each(function() {
						$(this).addClass('selected');
						$(this).addClass('selected' + index);
					});
					$('.sandbox-text .' + clazz).each(function() {
						$(this).addClass('selected');
						$(this).addClass('selected' + index);
					});
					sandbox$.board.update();
					sandbox$.board.update();
				}
			});
		}
	});

	$('.sandbox-text .figure').each(function() {
		var element = $(this);
		beautified = function(point) {
			return '<span class=\'point\'>' + point.replace(/_(\d*)/, '<sub>$1</sub>') + '</span>';
		};
		append_point_list = function(cls) {
			cls.split('__').slice(1).forEach(point => {
				element.append(beautified(point));
			});
		}
		element[0].classList.forEach(cls => {
			element.empty();
			if (cls.startsWith('tr__')) {
				element.append('△');
				append_point_list(cls);
			} else if (cls.startsWith('plg__')) {
				append_point_list(cls);
			} else if (cls.startsWith('ang__')) {
				element.append('∠');
				append_point_list(cls);
			} else if (cls.startsWith('ang4__')) {
				element.append('∠');
				points = cls.split('__').slice(1);
				element.append(beautified(points[0]));
				element.append(beautified(points[1]));
				element.append('<span class="angle-comma">,</span>');
				element.append(beautified(points[2]));
				element.append(beautified(points[3]));
			} else if (cls.startsWith('vec__')) {
				append_point_list(cls);
			} else if (cls.startsWith('ray__')) {
				append_point_list(cls);
			} else if (cls.startsWith('ln__')) {
				append_point_list(cls);
			} else if (cls.startsWith('seg__')) {
				append_point_list(cls);
			} else if (cls.startsWith('cyc__')) {
				element.append('↻');
				append_point_list(cls);
			} else if (cls.startsWith('pt__')) {
				append_point_list(cls);
			}
		});
	});
},

createTree: function(json) {
	var root = $('#sandbox-tree');

	var data = JSON.parse(json);
	var buildTree = function(root, index) {
		var obj = data[index];
		var item = $('<li/>');
		item.attr('priority', obj.priority);
		item.append('<span class="handler material-icons-outlined"/>');
		item.append(sandbox$.beautifiedLine(obj.property));
		item.append('<span class="implication">⇐</span>');
		item.append(sandbox$.beautifiedLine(obj.comment));
		if (obj.premises.length > 0) {
			var list = $('<ul/>');
			obj.premises.forEach(ind => { buildTree(list, ind); });
			item.append(list);
		}
		root.append(item);
	};
	var tree = $('<ul/>');
	buildTree(tree, 0);
	root.append(tree);

	root.find('li').each(function() {
		var element = $(this);
		if (element.find('ul')) {
			element.addClass('closed');
			element.removeClass('open');
			element.find('span.handler').first().click(function(e) {
				if (e.shiftKey) {
					if (element.hasClass('closed')) {
						element.find('.closed').removeClass('closed').addClass('open');
					} else if (element.hasClass('open')) {
						element.find('.open').removeClass('open').addClass('closed');
					}
				}
				element.toggleClass('open');
				element.toggleClass('closed');
				e.stopPropagation();
			});
		}
	});
},

setTitle: function(title) {
	window.document.title = title;
	$('#page-title').text(title);
},

setTask: function(json) {
	task = $('#sandbox-task');
	var data = JSON.parse(json);
	data.forEach(item => {
		line = $('<p/>');
		line.append(sandbox$.beautifiedLine(item));
		task.append(line);
	});
},

setReference: function(reference) {
	$('#sandbox-reference').html(reference);
},

toggleNonEssential: function() {
	var root = $('#sandbox-tree');
	var max_priority = 0;
	root.find('[priority]').each(function() {
		max_priority = Math.max(max_priority, $(this).attr('priority'));
	});
	var hideNonEssential = root.find('#checkbox').is(':checked');
	root.find('[priority]').each(function() {
		var hide = hideNonEssential && $(this).attr('priority') < max_priority;
		if (hide) {
			$(this).find('[priority]').each(function() {
				if ($(this).attr('priority') >= max_priority) {
					hide = false;
					return false;
				}
			});
		}
		$(this).css('display', hide ? 'none' : 'block');
	});
	root.find('li').each(function() {
		var list = $(this).find('ul').first();
		if (!list) {
			return;
		}
		var hasVisibleChildren = false;
		list.children().each(function() {
			if ($(this).css('display') != 'none') {
				hasVisibleChildren = true;
				return false;
			}
			return true;
		});
		if (hasVisibleChildren) {
			$(this).removeClass('empty');
		} else {
			$(this).addClass('empty');
		}
	});
	$('.chevron').each(function() {
		var chevron = $(this);
		chevron.addClass('chevron-animated')
		chevron.parent().click(function() {
			chevron.toggleClass('chevron-rotated');
		});
	});
}

};
