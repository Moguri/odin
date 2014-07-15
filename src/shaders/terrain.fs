#version 330

in vec4 vertex;
in vec3 normal;
in vec3 vertex_ws;
in vec3 light_pos;

uniform sampler2D selection_map;

out vec3 out_color;

const float grid_size = 1.0;
const float grid_width = 0.01;
const int map_size = 32;

const vec3 current_color = vec3(1.0);
const vec3 move_color = vec3(0.1, 0.1, 1.0);
const vec3 attack_color = vec3(1.0, 0.1, 0.1);

const int SEL_CUR = 1 << 0;
const int SEL_MOVE = 1 << 1;

void main()
{
	vec3 diffuse = vec3(0.5, 1.0, 0.0);
	float specular = 50.0;

	vec3 L = normalize(light_pos - vertex.xyz);
	vec3 N = normalize(normal);
	vec3 E = normalize(-vertex.xyz);
	vec3 R = normalize(-reflect(L, N));

	vec3 amb = vec3(0.1, 0.1, 0.1);

	vec2 pos = mod(vertex_ws.xy, grid_size);

	float line = 1.0;
	float offsets[4] = float[4](abs(pos.x - grid_size), pos.x,
								abs(pos.y - grid_size), pos.y);
	for (int i = 0; i < 4; ++i) {
		float width = offsets[i];
		if (width < grid_width)
		{
			width /= grid_width;
			line *= width;
		}
	}

	ivec2 index = ivec2(vertex_ws.xy / grid_size + ivec2(map_size / 2));
	index.y = map_size - index.y - 1;

	vec3 diff = diffuse;

	int selection = int(texelFetch(selection_map, index, 0).r * 255);

	vec3 sel_color = vec3(0.0);
	int sel_count = 0;
	if ((selection & SEL_MOVE) > 0) {
		sel_color += move_color;
		++sel_count;
	}
	if ((selection & SEL_CUR) > 0) {
		sel_color += current_color;
		++sel_count;
	}

	if (sel_count > 0) {
		sel_color /= sel_count;
		diff = mix(diff, sel_color, 1.0);
	}

	diff *= max(dot(N, L), 0.0);

	vec3 spec = vec3(1.0, 1.0, 1.0);
	spec *= pow(max(dot(R, E), 0.0), specular);

	out_color.rgb = (amb + diff + spec) * line;
	// out_color.rgb = sel_color;
}