varying vec4 vertex;
varying vec3 normal;
varying vec3 vertex_ws;
varying vec3 light_pos;



void main()
{
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
	vertex_ws = gl_Vertex.xyz;
	vertex = gl_ModelViewMatrix * gl_Vertex;
	normal = gl_NormalMatrix * gl_Normal;

	light_pos = (gl_ModelViewMatrix * vec4(12.1, -2.6, 3.8, 0.0)).xyz;
}