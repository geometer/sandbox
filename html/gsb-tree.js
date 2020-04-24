function setupTree() {
	root = document.getElementById('gsb-tree');
	root.querySelectorAll('span').forEach(item => {
		if (item.parentElement.nodeName.toLowerCase() == 'span') {
			return;
		}
		item.classList.forEach(cls => {
			var points = null;
			var segments = [];
			if (cls.startsWith('tr__')) {
				points = cls.split('__').slice(1, 4);
				segments = [
					[points[0], points[1], false],
					[points[0], points[2], false],
					[points[1], points[2], false]
				];
			} else if (cls.startsWith('ang__')) {
				points = cls.split('__').slice(1, 4);
				segments = [
					[points[1], points[0], true],
					[points[1], points[2], true]
				];
			} else if (cls.startsWith('vec__')) {
				points = cls.split('__').slice(1, 3);
				segments = [[points[0], points[1], false]];
			} else if (cls.startsWith('seg__')) {
				points = cls.split('__').slice(1, 3);
				segments = [[points[0], points[1], false]];
			} else if (cls.startsWith('pt__')) {
				points = cls.split('__').slice(1, 2);
			}
			if (points) {
				item.addEventListener('mouseover', function() {
					points.forEach(id => { idToPoint[id].highlight(); });
					segments.forEach(seg => {
						selectedSegments.push(board.create("line", [idToPoint[seg[0]], idToPoint[seg[1]]], {straightFirst:false, straightLast:seg[2], color:"#00E6E3", strokeWidth:1.5}));
					});
					root.querySelectorAll('.' + cls).forEach(elt => {elt.style.background = "#00E6E3";});
				});
				item.addEventListener('mouseleave', function() {
					points.forEach(id => { idToPoint[id].noHighlight(); });
					selectedSegments.forEach(obj => {board.removeObject(obj);});
					root.querySelectorAll('.' + cls).forEach(elt => {elt.style.background = null;});
				});
			}
		});
	});
	root.querySelectorAll('li').forEach(item => {
		if (item.querySelector('ul') == null) {
			return;
		}
		item.classList.add('closed');
		item.classList.remove('open');
		item.addEventListener('click', function(e) {
			this.classList.toggle('open');
			this.classList.toggle('closed');
			e.stopPropagation();
		});
	});
}
